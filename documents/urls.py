from django.urls import path
from .views import DocumentListView, DocumentDetailView, AskQuestionView, SummarizeDocumentView

urlpatterns = [
    path('', DocumentListView.as_view(), name='document-list'),
    path('<int:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    path('ask-question/', AskQuestionView.as_view(), name='ask-question'),
    path('<int:document_id>/summarize/', SummarizeDocumentView.as_view(), name='document-summarize'),
] 