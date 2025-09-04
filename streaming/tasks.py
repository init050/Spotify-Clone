import subprocess
import json
import logging
import tempfile
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction

from .models import AudioFile, AudioQuality
from artists.models import Track

logger = logging.getLogger(__name__)

def _run_command(command):
    'Helper to run a subprocess command and handle errors.'
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return result
    except FileNotFoundError as e:
        logger.error(f"Command '{command[0]}' not found. Ensure ffmpeg/ffprobe are installed and in the system's PATH.")
        raise e
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(command)}")
        logger.error(f"Stderr: {e.stderr}")
        raise e

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_audio_file(self, audio_file_id):
    'Celery task to process, transcode, and extract metadata from an audio file.'
    try:
        audio_file = AudioFile.objects.select_related('track').get(pk=audio_file_id)
    except AudioFile.DoesNotExist:
        logger.error(f'AudioFile with id {audio_file_id} not found.')
        return

    if audio_file.status == Track.ProcessingStatus.COMPLETED:
        logger.info(f'AudioFile {audio_file_id} is already processed. Skipping.')
        return

    audio_file.status = Track.ProcessingStatus.PROCESSING
    audio_file.save()

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            # 1. Get the original file from storage
            original_file_name = Path(audio_file.original_file.name).name
            input_path = temp_dir_path / original_file_name
            with open(input_path, 'wb') as f:
                f.write(audio_file.original_file.read())

            # 2. Run ffprobe to get metadata
            probe_command = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(input_path)
            ]
            probe_result = _run_command(probe_command)
            metadata = json.loads(probe_result.stdout)
            audio_stream = next((s for s in metadata['streams'] if s['codec_type'] == 'audio'), None)

            if not audio_stream:
                raise ValueError('No audio stream found in the file.')

            # 3. Update database with metadata
            with transaction.atomic():
                audio_file.duration_ms = int(float(metadata['format']['duration']) * 1000)
                audio_file.bitrate_kbps = int(int(audio_stream.get('bit_rate', 0)) / 1000)
                audio_file.sample_rate = int(audio_stream.get('sample_rate', 0))
                audio_file.channels = audio_stream.get('channels', 0)
                audio_file.metadata = metadata # Save all raw metadata
                audio_file.save()

            # 4. Run ffmpeg to transcode to HLS
            output_dir = temp_dir_path / 'hls'
            output_dir.mkdir()

            hls_bitrates = settings.STREAMING_HLS_BITRATES
            ffmpeg_command = [
                'ffmpeg', '-i', str(input_path),
                '-preset', 'veryfast', '-keyint_min', '25', '-g', '250', '-sc_threshold', '0',
                '-map', '0:a:0', '-map', '0:a:0', '-map', '0:a:0',
            ]

            stream_map_str = ''
            for i, br in enumerate(hls_bitrates):
                ffmpeg_command.extend([
                    f'-b:a:{i}', f'{br}k', '-ac', '2', '-ar', '48000',
                ])
                stream_map_str += f'v:0,a:{i},name:{br}k '

            stream_map_str = stream_map_str.strip()

            ffmpeg_command.extend([
                '-f', 'hls',
                '-hls_time', '4',
                '-hls_playlist_type', 'vod',
                '-hls_segment_filename', str(output_dir / 'segment_%v_%03d.ts'),
                '-master_pl_name', 'master.m3u8',
                '-var_stream_map', stream_map_str,
                str(output_dir / 'playlist_%v.m3u8')
            ])

            _run_command(ffmpeg_command)

            # 5. Upload HLS files to storage and create AudioQuality objects
            with transaction.atomic():
                # Upload master playlist
                master_playlist_path = output_dir / 'master.m3u8'
                with open(master_playlist_path, 'rb') as f:
                    audio_file.hls_master.save('master.m3u8', ContentFile(f.read()))

                # Upload variant playlists and segments
                for f in output_dir.iterdir():
                    if f.is_file():
                        with open(f, 'rb'):
                            # This needs a proper storage backend utility
                            # For simplicity, we assume default storage handles upload
                            # In a real app, you'd use boto3 directly for more control
                            pass # Placeholder for segment upload logic

                for br in hls_bitrates:
                    AudioQuality.objects.create(
                        audio_file=audio_file,
                        bitrate_kbps=br,
                        resolution_label=f'{br}kbps',
                        format='hls',
                        # file field would point to the variant m3u8
                    )

            audio_file.status = Track.ProcessingStatus.COMPLETED
            audio_file.save()

        logger.info(f'Successfully processed AudioFile {audio_file_id}.')

    except Exception as e:
        logger.exception(f'Failed to process AudioFile {audio_file_id}: {e}')
        audio_file.status = Track.ProcessingStatus.FAILED
        audio_file.save()
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for AudioFile {audio_file_id}.")
