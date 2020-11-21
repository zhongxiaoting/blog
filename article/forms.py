

# 文章的表单类
from django import forms

from article.models import ArticlePost


class ArticlePostForm(forms.ModelForm):
    class Meta:
        # 指明数据的来源
        model = ArticlePost
        # 定义表单包含的字段
        fields = ('title', 'body', 'tags', 'avatar')


