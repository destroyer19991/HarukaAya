#    Haruka Aya (A telegram bot project)
#    Copyright (C) 2017-2019 Paul Larsen
#    Copyright (C) 2019-2021 A Haruka Aita and Intellivoid Technologies project

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from telegram import Update
from telegram import MessageEntity
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, CallbackContext

from haruka import dispatcher
from haruka.modules.disable import DisableAbleCommandHandler, DisableAbleMessageHandler

from haruka.modules.sql import afk_sql as sql
from haruka.modules.users import get_user_id

from haruka.modules.tr_engine.strings import tld

AFK_GROUP = 7
AFK_REPLY_GROUP = 8


def afk(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    if not user:  # ignore channels
        return

    if user.id == 777000:
        return

    args = update.effective_message.text.split(None, 1)
    if len(args) >= 2:
        reason = args[1]
    else:
        reason = ""

    sql.set_afk(update.effective_user.id, reason)
    fname = update.effective_user.first_name
    update.effective_message.reply_text(
        tld(chat.id, "user_now_afk").format(fname))


def no_longer_afk(update: Update, context: CallbackContext):
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message

    if not user:  # ignore channels
        return

    res = sql.rm_afk(user.id)
    if res:
        if message.new_chat_members:  #dont say msg
            return
        firstname = update.effective_user.first_name
        try:
            message.reply_text(
                tld(chat.id, "user_no_longer_afk").format(firstname))
        except Exception:
            return


def reply_afk(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    userc = update.effective_user
    userc_id = userc.id
    if message.entities and message.parse_entities(
        [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]):
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION])

        chk_users = []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

            elif ent.type == MessageEntity.MENTION:
                user_id = get_user_id(message.text[ent.offset:ent.offset +
                                                   ent.length])
                if not user_id:
                    # Should never happen, since for a user to become AFK they must have spoken. Maybe changed username?
                    return

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

                try:
                    chat = bot.get_chat(user_id)
                except BadRequest:
                    print("Error: Could not fetch userid {} for AFK module".
                          format(user_id))
                    return
                fst_name = chat.first_name

            else:
                return

            check_afk(bot, update, user_id, fst_name, userc_id)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(bot, update, user_id, fst_name, userc_id)


def check_afk(bot, update, user_id, fst_name, userc_id):
    chat = update.effective_chat
    if sql.is_afk(user_id):
        user = sql.check_afk_status(user_id)
        if not user.reason:
            if int(userc_id) == int(user_id):
                return
            res = tld(chat.id, "status_afk_noreason").format(fst_name)
            update.effective_message.reply_text(res)
        else:
            if int(userc_id) == int(user_id):
                return
            res = tld(chat.id,
                      "status_afk_reason").format(fst_name, user.reason)
            update.effective_message.reply_text(res)


__help__ = True

AFK_HANDLER = DisableAbleCommandHandler("afk", afk, run_async=True)
AFK_REGEX_HANDLER = DisableAbleMessageHandler(
    Filters.regex("(?i)brb"), afk, friendly="afk", run_async=True
)
NO_AFK_HANDLER = MessageHandler(Filters.all & Filters.chat_type.groups, no_longer_afk, run_async=True)
AFK_REPLY_HANDLER = MessageHandler(Filters.all & Filters.chat_type.groups, reply_afk, run_async=True)

dispatcher.add_handler(AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REGEX_HANDLER, AFK_GROUP)
dispatcher.add_handler(NO_AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REPLY_HANDLER, AFK_REPLY_GROUP)
