from app import db
from app.main import bp
from app.main.forms import PostForm, EmptyForm, EditProfileForm, SearchForm
from app.models import Post, User
from app.translate import detect_language
from datetime import datetime
from flask import (
    flash, redirect, g, jsonify, current_app,
    render_template, request, url_for,
)
from flask_babel import _, get_locale as gl
from flask_login import current_user, login_required
from app.translate import translate


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        # 'g' is a container provided by flask that exists for the
        #  lifetime of the request. it is specific to each request.
        g.search_form = SearchForm()
    # using aliased get_locale from flask-babel
    g.locale = str(gl())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        language = detect_language(form.post.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    posts = (
        current_user.followed_posts()
                    .paginate(
                        page=page, error_out=False,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                    )
    )
    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None
    return render_template(
        'index.pug',
        title=_('Home Page'), form=form, posts=posts.items,
        next_url=next_url, prev_url=prev_url,
    )


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = (
        Post.query.order_by(Post.timestamp.desc())
                  .paginate(
                      page=page, error_out=False,
                      per_page=current_app.config['POSTS_PER_PAGE'],
                  )
    )
    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None
    return render_template(
        'index.pug',
        title=_('Explore'), posts=posts.items,
        next_url=next_url, prev_url=prev_url,
    )


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = (
        user.posts.order_by(Post.timestamp.desc())
                  .paginate(
                      page=page, error_out=False,
                      per_page=current_app.config['POSTS_PER_PAGE'],
                  )
    )
    next_url = url_for('main.user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template(
        'user.pug',
        user=user, posts=posts.items, form=form,
        next_url=next_url, prev_url=prev_url,
    )


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.pug', title=_('Edit Profile'), form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):

    form = EmptyForm()
    if form.validate_on_submit():

        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('main.user', username=username))

        current_user.follow(user)
        db.session.commit()
        flash(_('You are following %(username)s.', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        #  CSRF token is missing or invalid
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):

    form = EmptyForm()
    if form.validate_on_submit():

        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('main.user'), username=username)

        current_user.unfollow(user)
        db.session.commit()
        flash(_('You have unfollowed %(username)s.', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        # CSRF token is missing or invalid
        return redirect(url_for('main.index'))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({
        'text': translate(
            request.form['text'],
            request.form['source_language'],
            request.form['dest_language']
        )
    })


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))

    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(
        g.search_form.q.data, page,
        current_app.config['POSTS_PER_PAGE']
    )
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None

    return render_template(
        'search.pug',
        title=_('Search'), posts=posts,
        next_url=next_url, prev_url=prev_url
    )
