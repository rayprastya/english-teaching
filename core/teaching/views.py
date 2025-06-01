from django.views import View
from django.shortcuts import render
from core.utils.whisper import score_spelling

# Create your views here.
class RoomView(View):
    template_name = 'teaching/room.html'

    def get(self, request):
        return render(request, 'teaching/room.html')
    
    def post(self, request):
        score = None 
        transcribed = ""

        # if form.is_valid():
        transcribed, score = score_spelling(save_path, word)

        context = {
            # "form": form, # TODO: to use form from the template
            "score": score,
            "transcribed": transcribed
        }

        return render(request, self.template_name, context)
