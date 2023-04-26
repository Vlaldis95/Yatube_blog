from django.core.paginator import Paginator

SEARCH_POSTS = 10


def paginate_posts(request, posts):
    paginator = Paginator(posts, SEARCH_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
