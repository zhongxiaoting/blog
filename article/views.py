from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views import View

from article.models import ArticlePost, ArticleColumn

import markdown

# 引入刚才定义的ArticlePostForm表单类
from comment.forms import CommentForm
from comment.models import Comment
from .forms import ArticlePostForm
from django.core.paginator import Paginator
# 引入 Q 对象
from django.db.models import Q


# 文章列表（所有文章）
def article_list(request):
    search = request.GET.get('search')
    order = request.GET.get('order')
    column = request.GET.get('column')
    tag = request.GET.get('tag')
    # 初始化查询集
    article_list = ArticlePost.objects.all()

    # 用户搜索逻辑
    if search:
        # 用 Q 对象进行联合收索
        article_list = ArticlePost.objects.filter(
            Q(title__icontains=search) | Q(body__icontains=search)
        ).order_by('-total_views')
    else:
        # 将 search 参数重置为空
        search = ''
    # 栏目查询集
    if column is not None and column.isdigit():
        article_list = article_list.filter(column=column)
    # 标签查询集
    if tag and tag != 'None':
        article_list = article_list.filter(tags__name__in=[tag])

    # 查询集排序
    if order == 'total_views':
        article_list = article_list.order_by('-total_views')

    # 每页显示一篇文章
    paginator = Paginator(article_list, 3)
    # 获取 url 中得页码
    page = request.GET.get('page')
    # 将导航对象相应得页码内容返回给 articles
    articles = paginator.get_page(page)
    # 传递给模板
    context = {'articles': articles, 'order': order,
               'search': search, 'column': column, 'tag': tag}
    # render函数，载入模板，返回给context
    return render(request, 'article/list.html', context)


# 文章详情页
def article_detail(request, id):
    # 取出文章的详情页
    article = ArticlePost.objects.get(id=id)

    # 取出文章评论
    comments = Comment.objects.filter(article=id)

    # 浏览量+1
    article.total_views += 1
    article.save(update_fields=['total_views'])
    # 将markdown语法渲染成html样式
    md = markdown.Markdown(
        extensions=[
            # 包含 缩写、表格等常用扩展
            'markdown.extensions.extra',
            # 语法高亮扩展
            'markdown.extensions.codehilite',
            # 目录扩展
            'markdown.extensions.toc',
        ])
    article.body = md.convert(article.body)
    # 引入评论表单
    comment_form = CommentForm()
    # 传递给模板
    context = {'article': article, 'toc': md.toc, 'comments': comments, 'comment_form': comment_form}
    # 载入给模板，返回给context
    return render(request, 'article/detail.html', context)


# 文章的视图
# 检查登录
@login_required(login_url='/userprofile/login')
def article_create(request):
    # 判断用户是否提交数据
    if request.method == "POST":
        # 将提交的数据赋值到表单实例中
        article_post_form = ArticlePostForm(request.POST, request.FILES)
        # 判断提交的数据是否满足模型要求
        if article_post_form.is_valid():
            # 保存数据，暂时不提交到数据库中
            new_article = article_post_form.save(commit=False)
            # 将数据传入用户
            new_article.author = User.objects.get(id=request.user.id)
            if request.POST['column' ] != 'none':
                new_article.column = ArticleColumn.objects.get(id=request.POST['column'])
            # 将新文章保存到数据库中
            new_article.save()
            # 保存 tags 的多对多关系
            article_post_form.save_m2m()
            # 完成后返回到文章列表
            return redirect("article:article_list")
        # 如果数据不合法，返回错误信息
        else:
            return HttpResponse("表单内容有误，请重新填写")
    # 如果用户请求获取数据
    else:
        # 创建表单类实列
        article_post_form = ArticlePostForm()
        columns = ArticleColumn.objects.all()
        # 赋值上下文
        context = {'article_post_form': article_post_form, 'columns': columns}
        # 返回模板
        return render(request, 'article/create.html', context)


# 删除文章
def article_safe_delete(request, id):
    article = ArticlePost.objects.get(id=id)
    # 非作者用户不能删除
    if request.user != article.author:
        return HttpResponse("抱歉，你无权删除该文章")
    if request.method == 'POST':
        article.delete()
        return redirect("article:article_list")
    else:
        return HttpResponse("仅允许post请求")


# 提醒用户登录
@login_required(login_url='/userprofile/login/')
# 修改文章
def article_update(request, id):
    """
       更新文章的视图函数
       通过POST方法提交表单，更新titile、body字段
       GET方法进入初始表单页面
       id： 文章的 id
       """
    # 获取需要修改文章的id
    article = ArticlePost.objects.get(id=id)
    # 过滤非作者用户
    if request.user != article.author:
        return HttpResponse("抱歉，你无权修改改文章")
    # 判断用户是否为POST提交
    if request.method == 'POST':
        # 将提交的数据赋值到表单中
        article_post_form = ArticlePostForm(data=request.POST)
        # 判断提交的数据是否满足模型的要求
        if article_post_form.is_valid():
            # 保存修改的数据
            article.title = request.POST['title']
            article.body = request.POST['body']

            if request.POST['column'] != 'none':
                article.column = ArticleColumn.objects.get(id=request.POST['column'])
            else:
                article.column = None
            if request.FILES.get('avatar'):
                article.avatar = request.FILES.get('avatar')
            article.tags.set(*request.POST.get('tags').split(','), clear=True)
            article.save()
            # 完成后返回修改后的文章中
            return redirect('article:article_detail', id=id)
        # 如果数据不合法，报错
        else:
            return HttpResponse("表单数据有误，请重新输入")
    # 如果用户get请求获取数据
    else:
        # 创建表单实列
        article_post_form = ArticlePostForm()
        columns = ArticleColumn.objects.all()
        # 赋值上下文，将article文章对象也传进去，以便提取旧的内容
        context = {'article': article, 'article_post_form': article_post_form,
                   'columns': columns, 'tags': ','.join([x for x in article.tags.names()]),
                   }
        # 响应到模板
        return render(request, 'article/update.html', context)


# 点赞数统计
class IncreaseLikesView(View):
    def post(self, request, *args, **kwargs):
        article = ArticlePost.objects.get(id=kwargs.get('id'))
        article.likes += 1
        article.save()
        return HttpResponse('success')
