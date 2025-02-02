from MessagesByTimeGraph import plot_messages_by_time
from SentimentPredict import predict_sentiment, plot_sentiment_pie_chart
from WordsTop import create_frequency_dict_lemma
from VKInteraction import get_user_name, PEER_ID, get_messages_for_day
from Utils.TimeUtils import get_unix_time_range_previous_day
from AIResponse import get_answer
from Utils.StickerUtils import get_attachment
from Utils.ReactionsUtils import reactions_dict


def summarize_day(messages):
    """Обрабатывает и составляет краткий пересказ дня."""
    id_name_dict = dict()
    messages_list = list()
    for msg in messages:
        if not id_name_dict.get(msg['from_id']):
            id_name_dict[msg['from_id']] = get_user_name(msg['from_id'])
        if len(msg['text'].split(" ")) < 150:
            messages_list.append(msg['text'])

    message_string = "Вот все сообщения:\n\n"

    for msg in messages[::-1]:
        author_name = id_name_dict[msg['from_id']]
        if "Всего сообщений за день" not in msg['text']:
            message_string += f"{author_name}: {msg['text']}\n"

    word_stats = create_frequency_dict_lemma(" ".join(messages_list))
    top_words = "\n".join(
        [f"{word}: {count}" for word, count in sorted(word_stats.items(), key=lambda x: x[1], reverse=True)[:10]])
    return message_string, top_words


def calculate_user_stats(messages):
    """Собирает статистику по сообщениям пользователей."""
    user_message_count = {}
    user_word_count = {}

    for msg in messages:
        user_id = msg['from_id']
        text = msg['text']
        if 'Всего сообщений за день' not in text and 'Самый часто встречающийся стикер за день' not in text:
            user_word_count[user_id] = user_word_count.get(user_id, 0) + len(text.split())
            user_message_count[user_id] = user_message_count.get(user_id, 0) + 1

    top_users_by_messages = sorted(user_message_count.items(), key=lambda x: x[1], reverse=True)
    top_users_by_words = sorted(user_word_count.items(), key=lambda x: x[1], reverse=True)
    return top_users_by_messages, top_users_by_words


def get_top_sticker_url(messages):
    """Возвращает ссылку на топ-1 стикер"""
    url_dict = dict()
    for msg in messages:
        if len(msg['attachments']) != 0 and msg['attachments'][0].get('sticker'):
            url = msg['attachments'][0]['sticker']['images'][-3]['url']
            if not url_dict.get(url):
                url_dict[url] = 1
            else:
                url_dict[url] += 1

    most_common_url = 0
    occur_number = 0
    for key, value in url_dict.items():
        if value > occur_number:
            most_common_url = key
            occur_number = value

    return most_common_url


def get_stickers_count(messagse):
    count = 0
    for msg in messagse:
        if len(msg['attachments']) != 0 and msg['attachments'][0].get('sticker'):
            count += 1
    return count


def get_reactions_for_usernames(reactions_for_user):
    username_reaction_count_dict = {}
    for user_id in reactions_for_user.keys():
        sorted_reactions = dict(sorted(reactions_for_user[user_id].items(), key=lambda item: item[1], reverse=True))
        reactions_count_pics = {}
        for k, v in sorted_reactions.items():
            if k in reactions_dict:
                reactions_count_pics[reactions_dict[k]] = v
        username_reaction_count_dict[get_user_name(user_id)] = reactions_count_pics
    sorted_by_reactions_count_username = dict(sorted(username_reaction_count_dict.items(), key=lambda item: sum(
        reactions_count for reactions_count in item[1].values()), reverse=True))
    return dict(list(sorted_by_reactions_count_username.items())[:5])


def get_reactions_top(messages):
    reaction_counts = {}
    count = 0
    user_messages_reactions = {}
    for msg in messages:
        if 'reactions' in msg:
            if msg['from_id'] not in user_messages_reactions:
                user_messages_reactions[msg['from_id']] = {}
            reaction_on_msg_count = sum(reaction['count'] for reaction in msg['reactions'])
            count += reaction_on_msg_count
            for reaction in msg['reactions']:
                if reaction['reaction_id'] not in reaction_counts:
                    reaction_counts[reaction['reaction_id']] = 0
                reaction_counts[reaction['reaction_id']] += reaction['count']
                if reaction['reaction_id'] not in user_messages_reactions[msg['from_id']]:
                    user_messages_reactions[msg['from_id']][reaction['reaction_id']] = 0
                user_messages_reactions[msg['from_id']][reaction['reaction_id']] += reaction['count']
    reactions_count_pics = {}
    sorted_reactions = dict(sorted(reaction_counts.items(), key=lambda item: item[1], reverse=True))
    for k, v in sorted_reactions.items():
        if k in reactions_dict:
            reactions_count_pics[reactions_dict[k]] = v
    top_five_reactions = dict(list(reactions_count_pics.items())[:5])
    username_top_five_for_reactions_count = get_reactions_for_usernames(user_messages_reactions)
    return count, top_five_reactions, username_top_five_for_reactions_count


def report_message_prepare():
    medals = ["🥇", "🥈", "🥉", "     \u2006", "     \u2006", "     \u2006", "     \u2006", "     \u2006", "     \u2006",
              "     \u2006"]
    """Отправляет отчёт за день."""
    start_time, end_time = get_unix_time_range_previous_day()
    messages = get_messages_for_day(PEER_ID, start_time, end_time)

    message_summary, top_words = summarize_day(messages)
    top_users_by_messages, top_users_by_words = calculate_user_stats(messages)
    most_common_sticker_url = get_top_sticker_url(messages)
    sticker_attachment = get_attachment(most_common_sticker_url)
    stickers_count = get_stickers_count(messages)
    reactions_count, top_five_reactions, username_top_five_for_reactions_count = get_reactions_top(messages)

    total_messages = sum(count for i, count in top_users_by_messages)
    top_users_string = "\n".join(
        [f"{medals[i]} {get_user_name(user_id)}: {count} сообщений" for i, (user_id, count) in
         enumerate(top_users_by_messages[:5])]
    )
    top_words_string = "\n".join(
        [f"{medals[i]} {get_user_name(user_id)}: {count} слов" for i, (user_id, count) in
         enumerate(top_users_by_words[:5])]
    )

    top_words = "\n".join(f"{medals[i]} {line}" for i, line in enumerate(top_words.splitlines()))

    top_five_reactions_string: str = "\n".join(
        [f"{medals[i]} {key}: {value}" for i, (key, value) in enumerate(top_five_reactions.items())]
    )
    username_top_five_for_reactions_count_string: str = "\n".join(
        [
            f"{medals[i]} {user}: {sum(reactions.values())} \n{medals[3]}{', '.join([f'{emoji}: {num}' for emoji, num in reactions.items()])}\n"
            for i, (user, reactions) in enumerate(username_top_five_for_reactions_count.items())]
    )

    plot_messages_by_time(messages)

    sentiment_counts = predict_sentiment(messages)
    plot_sentiment_pie_chart(sentiment_counts)

    # Удаляем прошедший контекст рандомным вопросом
    get_answer("Какую еду любят в японии?")

    # Получаем
    gpt_summary = get_answer(message_summary)

    return (total_messages, top_users_string, top_words_string, top_words, gpt_summary, sticker_attachment,
            stickers_count, reactions_count, top_five_reactions_string, username_top_five_for_reactions_count_string)
