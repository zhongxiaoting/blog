from django.contrib.auth.models import User
from django.db import models

# Create your models here.

# 博客文章数据模型
from django.urls import reverse
from django.utils import timezone
from taggit.managers import TaggableManager
from PIL import Image
# 引入imagekit
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFit


class ArticleColumn(models.Model):
    """
    栏目的MOdel
    """
    # 栏目标题
    title = models.CharField(max_length=100, blank=True)
    # 创建时间
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title


class ArticlePost(models.Model):
    # 文章作者
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    # 文章栏目的“一对多”外键
    column = models.ForeignKey(
        ArticleColumn,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='article'
    )

    # 文章标签
    tags = TaggableManager(blank=True)

    # 文章标题
    title = models.CharField(max_length=100)

    # 文章标题图
    avatar = models.ImageField(upload_to='article/%Y%m%d/', blank=True)

    # 文章正文
    body = models.TextField()

    # 文章阅读数
    total_views = models.PositiveIntegerField(default=0)

    # 文章创建时间
    created = models.DateTimeField(default=timezone.now)

    # 文章更新时间
    updated = models.DateTimeField(auto_now=True)

    # 文章点赞数统计
    likes = models.PositiveIntegerField(default=0)

    # 内部类 class Meta 用于给 model 定义元数据
    class Meta:
        ordering = ('-created',)

    # 返回文章的标题
    def __str__(self):
        return self.title

    # 获取文章地址
    def get_absolute_url(self):
        return reverse('article:article_detail', args=[self.id])

    # 保存时处理图片
    def save(self, *args, **kwargs):
        # 调用原有的 save() 的功能
        article = super(ArticlePost, self).save(*args, **kwargs)
        # 固定宽度缩放图片大小
        if self.avatar and not kwargs.get('update_fields'):
            image = Image.open(self.avatar)
            (x, y) = image.size
            new_x = 400
            new_y = int(new_x * (y / x))
            resized_image = image.resize((new_x, new_y), Image.ANTIALIAS)
            resized_image.save(self.avatar.path)
        return article
