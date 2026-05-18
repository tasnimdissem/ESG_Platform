from __future__ import annotations

import io
import logging
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from flask import current_app
from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_FORMATS = {'PNG', 'JPEG', 'JPG', 'WEBP'}
FORMAT_TO_EXTENSION = {
    'PNG': ('png', 'image/png'),
    'JPEG': ('jpg', 'image/jpeg'),
    'JPG': ('jpg', 'image/jpeg'),
    'WEBP': ('webp', 'image/webp'),
}


def _get_s3_client():
    region = current_app.config.get('AWS_REGION') or current_app.config.get('AWS_S3_REGION') or None
    endpoint_url = current_app.config.get('AWS_S3_ENDPOINT_URL') or None
    return boto3.client('s3', region_name=region, endpoint_url=endpoint_url)


def _build_public_url(bucket: str, key: str) -> str:
    base_url = (current_app.config.get('AWS_S3_PUBLIC_BASE_URL') or '').strip().rstrip('/')
    if base_url:
        return f'{base_url}/{key}'

    endpoint_url = (current_app.config.get('AWS_S3_ENDPOINT_URL') or '').strip().rstrip('/')
    if endpoint_url:
        return f'{endpoint_url}/{bucket}/{key}'

    region = (current_app.config.get('AWS_REGION') or current_app.config.get('AWS_S3_REGION') or 'us-east-1').strip()
    if region == 'us-east-1':
        return f'https://{bucket}.s3.amazonaws.com/{key}'
    return f'https://{bucket}.s3.{region}.amazonaws.com/{key}'


def _resize_avatar_image(file_bytes: bytes) -> tuple[bytes, str, str]:
    try:
        image = Image.open(io.BytesIO(file_bytes))
    except UnidentifiedImageError as exc:
        raise ValueError('Format d’image invalide') from exc

    image_format = (image.format or 'PNG').upper()
    if image_format not in ALLOWED_IMAGE_FORMATS:
        image_format = 'PNG'

    max_size = int(current_app.config.get('AVATAR_IMAGE_MAX_SIZE', 512))
    if image.mode not in ('RGB', 'RGBA'):
        image = image.convert('RGBA' if image_format == 'PNG' else 'RGB')

    image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    output = io.BytesIO()
    extension, content_type = FORMAT_TO_EXTENSION[image_format]
    if image_format in {'JPEG', 'JPG'} and image.mode != 'RGB':
        image = image.convert('RGB')

    save_kwargs = {'optimize': True}
    if image_format == 'JPEG':
        save_kwargs['quality'] = 88

    image.save(output, format='JPEG' if image_format == 'JPEG' else image_format, **save_kwargs)
    output.seek(0)
    return output.getvalue(), extension, content_type


def upload_user_avatar(*, user_id: int, upload: FileStorage) -> tuple[str, str]:
    if upload is None or not upload.filename:
        raise ValueError('Aucun fichier image fourni')

    raw_bytes = upload.read()
    if not raw_bytes:
        raise ValueError('Fichier image vide')

    max_bytes = int(current_app.config.get('AVATAR_MAX_UPLOAD_BYTES', 5 * 1024 * 1024))
    if len(raw_bytes) > max_bytes:
        raise ValueError('L’image dépasse la taille maximale autorisée')

    resized_bytes, extension, content_type = _resize_avatar_image(raw_bytes)

    bucket = (current_app.config.get('AWS_S3_BUCKET') or '').strip()
    if not bucket:
        raise RuntimeError('Le bucket S3 des avatars n’est pas configuré')

    avatar_key = f'avatars/users/{user_id}/{uuid4().hex}.{extension}'
    s3_client = _get_s3_client()
    try:
        s3_client.upload_fileobj(
            io.BytesIO(resized_bytes),
            bucket,
            avatar_key,
            ExtraArgs={'ContentType': content_type},
        )
    except (BotoCoreError, ClientError) as exc:
        logger.exception('Impossible de téléverser l’avatar vers S3')
        raise RuntimeError('Impossible de téléverser l’avatar') from exc

    return avatar_key, _build_public_url(bucket, avatar_key)


def delete_user_avatar(avatar_key: str | None) -> None:
    if not avatar_key:
        return

    bucket = (current_app.config.get('AWS_S3_BUCKET') or '').strip()
    if not bucket:
        return

    try:
        _get_s3_client().delete_object(Bucket=bucket, Key=avatar_key)
    except (BotoCoreError, ClientError):
        logger.warning('Impossible de supprimer l’ancien avatar S3: %s', avatar_key)