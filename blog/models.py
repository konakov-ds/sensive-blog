from django.db import models
from django.db.models import Count, Prefetch
from django.urls import reverse
from django.contrib.auth.models import User


class PostQuerySet(models.QuerySet):

    def year(self, year):
        posts_at_year = self.filter(published_at__year=year)\
            .order_by('published_at')
        return posts_at_year

    def popular(self):
        popular_posts = self\
            .annotate(num_likes=Count('likes', distinct=True))
        return popular_posts.order_by('-num_likes')

    def fetch_with_comments_count(self):
        posts_ids = [post.id for post in self]
        posts_with_comments = Post.objects.filter(id__in=posts_ids) \
            .annotate(num_comments=Count('comments'))
        ids_and_comments = dict(posts_with_comments
                                .values_list('id', 'num_comments'))
        for post in self:
            post.num_comments = ids_and_comments[post.id]
        return self

    def fetch_tags_with_posts_count(self):
        prefetch = Prefetch('tags', queryset=Tag.objects
                            .annotate(num_posts=Count('posts')))
        return self.prefetch_related(prefetch)


class TagQuerySet(models.QuerySet):

    def popular(self):
        popular_tags = self.annotate(num_posts=Count('posts'))\
            .order_by('-num_posts')
        return popular_tags


class Post(models.Model):

    objects = PostQuerySet.as_manager()

    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'


class Tag(models.Model):

    objects = TagQuerySet.as_manager()

    title = models.CharField('Тег', max_length=20, unique=True)

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class Comment(models.Model):

    post = models.ForeignKey(
        'Post',
        related_name='comments',
        on_delete=models.CASCADE,
        verbose_name='Пост, к которому написан')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
