from django import forms

class UploadForm(forms.Form):
    image = forms.ImageField(required=False)
    video = forms.FileField(required=False)
    rtsp_url = forms.CharField(label="RTSP-ссылка", required=False)
