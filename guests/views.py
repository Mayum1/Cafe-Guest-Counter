from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.conf import settings
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from .forms import UploadForm
from .models import DetectionHistory
from .yolo_utils import count_people, process_video, process_rtsp
import os

def index(request):
    count = None
    result_url = None

    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data.get('image')
            video = form.cleaned_data.get('video')
            rtsp_url = form.cleaned_data.get('rtsp_url')

            if image:
                temp_instance = DetectionHistory(image=image)
                temp_instance.save()
                path = temp_instance.image.path
                count, result_path = count_people(path)

            elif video:
                video_name = video.name
                save_path = os.path.join('media/uploads', video_name)
                with open(save_path, 'wb+') as f:
                    for chunk in video.chunks():
                        f.write(chunk)
                count, result_path = process_video(save_path)

            elif rtsp_url:
                count, result_path = process_rtsp(rtsp_url)

            else:
                return render(request, 'guests/index.html', {
                    'form': form,
                    'count': None,
                    'result_url': None,
                    'error': 'Нужно загрузить изображение, видео или вставить RTSP-ссылку'
                })

            if result_path:
                result_url = result_path.replace('\\', '/').replace('media/', '/media/')

            return render(request, 'guests/index.html', {
                'form': form,
                'count': count,
                'result_url': result_url
            })

    else:
        form = UploadForm()
    return render(request, 'guests/index.html', {'form': form, 'count': count})

@csrf_exempt
def process_image_ajax(request):
    if request.method == 'POST':
        image_file = request.FILES.get('image')
        if not image_file:
            return JsonResponse({'error': 'Файл изображения не получен'}, status=400)

        path = default_storage.save('uploads/' + image_file.name, image_file)
        full_path = os.path.join(settings.MEDIA_ROOT, path)
        count, result_path = count_people(full_path)

        # Сохраняем историю
        DetectionHistory.objects.create(
            request_type='image',
            file_path=path,
            guest_count=count
        )

        result_url = result_path.replace('\\', '/').replace('media/', '/media/')
        return JsonResponse({'count': count, 'result_url': result_url})

@csrf_exempt
def process_video_ajax(request):
    if request.method == 'POST':
        video_file = request.FILES.get('video')
        if not video_file:
            return JsonResponse({'error': 'Файл видео не получен'}, status=400)

        path = default_storage.save('uploads/' + video_file.name, video_file)
        full_path = os.path.join(settings.MEDIA_ROOT, path)
        count, result_path = process_video(full_path)

        DetectionHistory.objects.create(
            request_type='video',
            file_path=path,
            guest_count=count
        )

        result_url = result_path.replace('\\', '/').replace('media/', '/media/')
        return JsonResponse({'count': count, 'result_url': result_url})

@csrf_exempt
def process_rtsp_ajax(request):
    if request.method == 'POST':
        rtsp_url = request.POST.get('rtsp_url')
        if not rtsp_url:
            return JsonResponse({'error': 'RTSP-ссылка отсутствует'}, status=400)

        count, result_path = process_rtsp(rtsp_url)

        DetectionHistory.objects.create(
            request_type='rtsp',
            file_path=rtsp_url,
            guest_count=count
        )

        result_url = result_path.replace('\\', '/').replace('media/', '/media/') if result_path else ''
        return JsonResponse({'count': count, 'result_url': result_url})

def download_report(request):
    buffer = BytesIO()
    font_path = os.path.join(settings.BASE_DIR, 'fonts', 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
    font_path = os.path.join(settings.BASE_DIR, 'fonts', 'DejaVuSans-Bold.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', font_path))
    p = canvas.Canvas(buffer)

    p.setFont("DejaVuSans-Bold", 14)
    p.drawString(100, 800, "Отчёт по подсчёту гостей")
    p.setFont("DejaVuSans", 12)

    y = 770
    for entry in DetectionHistory.objects.order_by('-timestamp'):
        line = f"{entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {entry.get_request_type_display()} | гостей: {entry.guest_count}"
        if entry.file_path:
            line += f" | файл: {entry.file_path}"
        p.drawString(50, y, line)
        y -= 20
        if y < 50:
            p.showPage()
            y = 800

    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='guest_report.pdf')
