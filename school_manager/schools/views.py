from django.template import RequestContext, loader
from django.http import HttpResponse
# Create your views here.
from django.views.generic import ListView, DetailView
from schools.models import School

class SchoolList(ListView):
    model = School

class SchoolDetail(DetailView):
	model = School

def home(request):
	template = loader.get_template('schools/index.html')
	context = RequestContext(request, {
	})
	return HttpResponse(template.render(context))


