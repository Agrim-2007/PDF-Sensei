from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'title', 'file', 'extracted_text', 'created_at', 'updated_at')
        read_only_fields = ('id', 'extracted_text', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class QuestionSerializer(serializers.Serializer):
    document_id = serializers.IntegerField()
    question = serializers.CharField() 