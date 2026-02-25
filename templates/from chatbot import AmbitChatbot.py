from chatbot import AmbitChatbot
bot = AmbitChatbot()
bot.db.users.update_one(
    {'email': 'alice@amity.edu', 'college_id': 'amity'},
    {'$set': {'role': 'admin'}}
)
print('promoted alice@amity.edu -> admin')
