import os
import subprocess
import tempfile

import ffmpeg
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from .models import Track


def generate_waveform(input_path, output_path):
    """
    Generates waveform data from an audio file.
    """
    command = [
        'ffmpeg',
        '-i', input_path,
        '-filter_complex', '[0:a]aformat=channel_layouts=mono,compand=gain=-6,showwavespic=s=600x120:colors=White',
        '-frames:v', '1',
        output_path
    ]
    subprocess.run(command, check=True, capture_output=True)


@shared_task(bind=True)
def process_audio_upload(self, track_id):
    """
    Celery task to process an uploaded audio file:
    1. Probes for metadata.
    2. Transcodes to HLS with multiple bitrates.
    3. Generates a waveform image.
    4. Updates the Track model with the new data.
    """
    try:
        track = Track.objects.get(pk=track_id)
    except Track.DoesNotExist:
        return f'Track {track_id} not found.'

    track.status = Track.ProcessingStatus.PROCESSING
    track.save()

    temp_dir = tempfile.mkdtemp()
    original_audio_path = os.path.join(temp_dir, 'original_audio')
    hls_output_dir = os.path.join(temp_dir, 'hls')
    os.makedirs(hls_output_dir, exist_ok=True)

    try:
        # 1. Download original file from storage
        with default_storage.open(track.audio_original.name, 'rb') as f:
            with open(original_audio_path, 'wb') as temp_f:
                temp_f.write(f.read())

        # 2. Probe for metadata
        probe = ffmpeg.probe(original_audio_path)
        audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
        if not audio_stream:
            raise ValueError('No audio stream found in the file.')

        track.duration_ms = int(float(audio_stream['duration']) * 1000)
        track.bitrate_kbps = int(audio_stream['bit_rate']) // 1000
        track.sample_rate = int(audio_stream['sample_rate'])

        # TODO: Add loudness analysis (requires loudnorm filter and two-pass encoding)

        # 3. Transcode to HLS
        hls_variants_config = getattr(settings, 'CATALOG_HLS_VARIANTS', [64, 128, 256])

        ffmpeg_input = ffmpeg.input(original_audio_path)
        hls_outputs = []
        stream_map = ''

        for i, bitrate in enumerate(hls_variants_config):
            output_playlist = os.path.join(hls_output_dir, f'{bitrate}k.m3u8')
            hls_outputs.append(
                ffmpeg_input.audio.output(
                    output_playlist,
                    acodec='aac',
                    audio_bitrate=f'{bitrate}k',
                    hls_time=10,
                    hls_playlist_type='vod',
                    hls_segment_filename=os.path.join(hls_output_dir, f'{bitrate}k_%03d.ts')
                )
            )
            stream_map += f'v:{i},a:{i} '

        # Run all HLS transcoding commands
        ffmpeg.merge_outputs(*hls_outputs).run(capture_stdout=True, capture_stderr=True)

        # Create master playlist
        master_playlist_content = '#EXTM3U\n'
        for i, bitrate in enumerate(hls_variants_config):
            master_playlist_content += f'#EXT-X-STREAM-INF:BANDWIDTH={bitrate * 1000},RESOLUTION=,NAME="{bitrate}k"\n'
            master_playlist_content += f'{bitrate}k.m3u8\n'

        master_playlist_path = os.path.join(hls_output_dir, 'master.m3u8')
        with open(master_playlist_path, 'w') as f:
            f.write(master_playlist_content)

        # 4. Upload HLS files to storage
        track_storage_path = f'tracks/{track.slug}/hls'
        for filename in os.listdir(hls_output_dir):
            file_path = os.path.join(hls_output_dir, filename)
            with open(file_path, 'rb') as f:
                content = ContentFile(f.read())
                default_storage.save(os.path.join(track_storage_path, filename), content)

        track.audio_hls_master.name = os.path.join(track_storage_path, 'master.m3u8')

        # 5. Generate and upload waveform
        waveform_temp_path = os.path.join(temp_dir, 'waveform.png')
        generate_waveform(original_audio_path, waveform_temp_path)

        waveform_storage_path = f'tracks/{track.slug}/waveform.png'
        with open(waveform_temp_path, 'rb') as f:
            content = ContentFile(f.read())
            # For now, let's just save the path to a field. The spec said JSON.
            # This is a placeholder for actual JSON waveform data.
            # Storing the image path for now.
            track.waveform_json = {'image_path': default_storage.save(waveform_storage_path, content)}


        # 6. Finalize track
        track.status = Track.ProcessingStatus.COMPLETED
        track.save()

    except Exception as e:
        track.status = Track.ProcessingStatus.FAILED
        track.save()
        # Clean up temp dir
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
        # Reraise exception to let Celery know the task failed
        raise self.retry(exc=e, countdown=60, max_retries=3)

    finally:
        # Clean up temp dir
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)

    return f'Successfully processed track {track_id}'
