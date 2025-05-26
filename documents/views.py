from django.shortcuts import render
import fitz
import google.generativeai as genai
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Document
from .serializers import DocumentSerializer, QuestionSerializer
import traceback

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

class DocumentListView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        document = serializer.save()
        # Extract text from PDF
        if document.file.name.endswith('.pdf'):
            try:
                pdf_document = fitz.open(document.file.path)
                text = ""
                for page in pdf_document:
                    text += page.get_text()
                document.extracted_text = text
                document.save()
            except Exception as e:
                print(f"Error extracting text: {str(e)}")

class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

class AskQuestionView(generics.CreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document_id = serializer.validated_data['document_id']
        question = serializer.validated_data['question'].lower().strip()

        # Check for appreciative phrases
        if any(phrase in question for phrase in ['nice work', 'noice work', 'good job', 'thanks']):
            return Response({"answer": "Thanks!"})

        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if not document.extracted_text:
            return Response(
                {"error": "No text content available for this document"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Prepare the prompt for Gemini
            prompt = f"""Answer the following question based on the document content. Don't deviate from the document content, but if there are some small questions you can try to answer them, If the question cannot be answered from the document, state that you cannot find the answer in the document. If you are appreciated then show some gratitude. (you can try to keep a record of the questions and answers and try to improve your answer based on the feedback) (you can also try to keep a record for word count and line count) (remeber not to deviate from the document content but can answer simple basic questions, and you should know about yourself what are you). \n\nDocument content:\n{document.extracted_text}\n\nQuestion:\n{question}"""

            # Generate response using Gemini
            response = model.generate_content(prompt)
            answer = response.text.strip()

            return Response({"answer": answer})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Error generating answer: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SummarizeDocumentView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        document_id = self.kwargs['document_id']

        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if not document.extracted_text:
            return Response(
                {"error": "No text content available for this document"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Prepare the prompt for Gemini for summarization
            prompt = f"""Provide a brief summary of the following document content according to the size of the document in text format (dont give options just one simple summary should cover all the major points (according to the size and content of the document)):

Document content:
{document.extracted_text}
"""

            # Generate summary using Gemini
            response = model.generate_content(prompt)
            summary = response.text

            return Response({"summary": summary})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Error generating summary: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
