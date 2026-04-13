from django.contrib import admin

from apps.chats.models import BlockList, Call, Chat, Message, MessageFiles, MessageReaction

admin.site.register(Chat)
admin.site.register(BlockList)
admin.site.register(MessageReaction)
admin.site.register(Call)
admin.site.register(MessageFiles)
admin.site.register(Message)
