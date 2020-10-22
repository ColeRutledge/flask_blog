const set_message_count = n => {
    $('#message_count').text(n)
    $('#message_count').css('visibility', n ? 'visible' : 'hidden')
}


function translate(sourceElem, destElem, sourceLang, destLang) {
    $(destElem).html(`<img src="{{ url_for('static', filename='loading.gif') }}">`)
    $.post('/translate', {
        text: $(sourceElem).text(),
        source_language: sourceLang,
        dest_language: destLang
    }).done(function(response) {
        $(destElem).text(response['text'])
    }).fail(function() {
        $(destElem).text("{{ _('Error: Could not contact server.') }}")
    })
}


window.addEventListener('DOMContentLoaded', () => {
    if (auth) {
        $(function() {
            var since = 0
            setInterval(function() {
                $.ajax(`${url}?since=${since}`).done(
                    function(notifications) {
                        for (var i = 0; i < notifications.length; i++) {
                            if (notifications[i].name == 'unread_message_count') {
                                set_message_count(notifications[i].data)
                            }
                            since = notifications[i].timestamp
                        }
                    }
                )
            }, 10000)
        })
    }

    $(function(){
        var timer = null
        var xhr = null
        $('.user_popup').hover(
            function(event) {
                // mouse in event handler
                var elem = $(event.currentTarget)
                timer = setTimeout(function() {
                    timer = null
                    // popup logic goes here
                    xhr = $.ajax(
                        '/user/' + elem.first().text().trim() + '/popup').done(
                            function(data) {
                                xhr = null
                                // create and display popup here
                                elem.popover({
                                    trigger: 'manual',
                                    html: true,
                                    animation: false,
                                    container: elem,
                                    content: data,
                                }).popover('show')
                                flask_moment_render_all()
                            }
                        )
                }, 1000)
            },
            function(event) {
                // mouse out event handler
                var elem = $(event.currentTarget)
                if (timer) {
                    clearTimeout(timer)
                    timer = null
                }
                else if (xhr) {
                    xhr.abort()
                    xhr = null
                }
                else {
                    // destroy popup here
                    elem.popover('destroy')
                }
            }
        )
    })
})
