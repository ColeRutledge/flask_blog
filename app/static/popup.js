window.addEventListener('DOMContentLoaded', () => {

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
