import logging
from celery import shared_task
from django.db import transaction
from .models import Playlist

from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO
import requests

logger = logging.getLogger(__name__)

@shared_task
def rebalance_positions(playlist_id):
    """
    Rebalances the position of tracks in a playlist to ensure a consistent gap.
    """
    try:
        playlist = Playlist.objects.get(id=playlist_id)
        tracks = playlist.tracks.order_by('position')

        with transaction.atomic():
            for i, track in enumerate(tracks):
                new_position = (i + 1) * 1000
                if track.position != new_position:
                    track.position = new_position
                    track.save(update_fields=['position'])
        logger.info(f"Successfully rebalanced positions for playlist {playlist_id}")
        return True
    except Playlist.DoesNotExist:
        logger.warning(f"Playlist with id {playlist_id} does not exist for rebalancing.")
        return False
    except Exception as e:
        logger.error(f"Error rebalancing playlist {playlist_id}: {e}", exc_info=True)
        return False


@shared_task
def generate_playlist_collage(playlist_id):
    """
    Generates a 2x2 collage from the album covers of the first 4 tracks
    and sets it as the playlist's cover image.
    """
    try:
        playlist = Playlist.objects.get(id=playlist_id)
        if playlist.cover_image:
            logger.info(f"Playlist {playlist_id} already has a cover image. Skipping collage generation.")
            return

        tracks_with_covers = []
        for pt in playlist.tracks.order_by('position').select_related('track__album')[:10]:
            if pt.track.album and pt.track.album.cover:
                tracks_with_covers.append(pt.track.album.cover)
            if len(tracks_with_covers) == 4:
                break

        if not tracks_with_covers:
            logger.warning(f"No tracks with cover art found for playlist {playlist_id}.")
            return

        images = []
        for cover in tracks_with_covers:
            try:
                # Assuming covers are accessible via URL. If they are local files, this needs adjustment.
                response = requests.get(cover.url)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content)).resize((200, 200))
                images.append(img)
            except Exception as e:
                logger.error(f"Could not open image {cover.url} for playlist {playlist_id}: {e}")
                continue

        if not images:
            return

        # Create a 2x2 collage
        collage_size = 400
        collage = Image.new('RGB', (collage_size, collage_size))

        if len(images) > 0:
            collage.paste(images[0], (0, 0))
        if len(images) > 1:
            collage.paste(images[1], (200, 0))
        if len(images) > 2:
            collage.paste(images[2], (0, 200))
        if len(images) > 3:
            collage.paste(images[3], (200, 200))

        # Save the collage to a buffer
        buffer = BytesIO()
        collage.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)

        # Save buffer to playlist's cover_image field
        file_name = f'{playlist.slug}_collage.jpg'
        playlist.cover_image.save(file_name, ContentFile(buffer.getvalue()), save=True)

        logger.info(f"Successfully generated and saved collage for playlist {playlist_id}")

    except Playlist.DoesNotExist:
        logger.warning(f"Playlist with id {playlist_id} does not exist for collage generation.")
    except Exception as e:
        logger.error(f"Error generating collage for playlist {playlist_id}: {e}", exc_info=True)
