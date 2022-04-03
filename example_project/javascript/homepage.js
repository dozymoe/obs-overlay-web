const MAXIMUM_MESSAGES = 30;

const ChatMessages = {
    chat: [],

    oninit()
    {
        const socket = new WebSocket('ws://localhost:8282/ws');
        socket.addEventListener('message', event =>
                {
                    while (this.chat.length >= MAXIMUM_MESSAGES)
                    {
                        this.chat.shift();
                    }
                    this.chat.push(JSON.parse(event.data));
                    m.redraw();
                });
    },

    view(vnode)
    {
        return m.fragment(null, this.chat.map(item =>
            {
                return m('li', [
                    m('strong', item.author),
                    item.text]);
            }));
    },
}


function onload()
{
    console.log('Hi!');
    for (let el of document.querySelectorAll('.chat-messages'))
    {
        m.mount(el, ChatMessages);
    }
}
if (document.readyState !== 'loading') setTimeout(onload, 0);
else document.addEventListener('DOMContentLoaded', onload);
