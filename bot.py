from telethon.sync import TelegramClient, events
from telethon.tl.types import ChannelParticipantsAdmins, ChannelParticipantsBots, ChannelParticipantsKicked, ChannelParticipantsBanned, ChannelParticipantsSearch, InputChannel, InputChannelEmpty
from telethon.tl.functions.account import UpdateProfileRequest
import asyncio
import time
import pytz
import speedtest
import datetime
import os

api_id = 'your_id_api'
api_hash = 'you_hash_api'

client = TelegramClient('session_name', api_id, api_hash)

target_chat_id = None
fake_typing_task = None
owner_id = 'your_id'

unread_messages = {}

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if str(event.sender_id) != owner_id:
        return
    await event.respond('Bot is active! Send /fake_typing to start fake typing.')

@client.on(events.NewMessage(pattern='/fake_typing'))
async def fake_typing(event):
    if str(event.sender_id) != owner_id:
        return
    global target_chat_id
    if target_chat_id:
        chat_id = target_chat_id
        await event.respond('Fake typing started.')
        await start_fake_typing(chat_id)
    else:
        await event.respond('Please set a target chat ID using /setid command.')

async def start_fake_typing(chat_id):
    global fake_typing_task
    while True:
        async with client.action(chat_id, 'typing'):
            await asyncio.sleep(5)

@client.on(events.NewMessage(pattern=r'/setid\s+(\d+)'))
async def set_id(event):
    if str(event.sender_id) != owner_id:
        return
    global target_chat_id
    chat_id = event.pattern_match.group(1)
    if chat_id:
        target_chat_id = int(chat_id)
        with open('zall.txt', 'w') as file:
            file.write(str(target_chat_id))
        await event.respond('Target chat ID set successfully.')
    else:
        await event.respond('Please provide a valid chat ID.')

@client.on(events.NewMessage(pattern=r'/groupinfo\s+(\S+)'))
async def group_info(event):
    if str(event.sender_id) != owner_id:
        return
    group_link = event.pattern_match.group(1)
    try:
        entity = await client.get_entity(group_link)
        if entity:
            info_text = f'Nama Grup: {entity.title}\n'
            info_text += f'Jumlah Member: {await get_total_members(entity)}\n'
            info_text += f'Jumlah member yang sedang online: {await get_online_members(entity)}\n'
            info_text += f'Jumlah admin grup: {await get_admin_count(entity)}\n'
            info_text += f'Jumlah pengguna telegram premium yang ada di grup: {await get_premium_users_count(entity)}\n'
            await event.respond(info_text)
        else:
            await event.respond('Grup tidak ditemukan.')
    except Exception as e:
        await event.respond(f'Error: {e}')

async def get_total_members(entity):
    try:
        participants = await client.get_participants(entity)
        return len(participants)
    except Exception as e:
        return "Error: " + str(e)

async def get_online_members(entity):
    try:
        participants = await client.get_participants(entity)
        online_count = sum(1 for user in participants if user.status == 'online')
        return online_count
    except Exception as e:
        return "Error: " + str(e)

async def get_admin_count(entity):
    try:
        admins = await client.get_participants(entity, filter=ChannelParticipantsAdmins)
        return len(admins)
    except Exception as e:
        return "Error: " + str(e)

async def get_premium_users_count(entity):
    try:
        participants = await client.get_participants(entity)
        premium_count = sum(1 for user in participants if user.premium)
        return premium_count
    except Exception as e:
        return "Error: " + str(e)

@client.on(events.NewMessage(pattern='/status'))
async def get_status(event):
    if str(event.sender_id) != owner_id:
        return
    global target_chat_id
    with open('zall.txt', 'r') as file:
        saved_chat_id = file.read()
    if saved_chat_id:
        response = f'ID Target: {saved_chat_id}\nRequest Date: {datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")}\nLast Chat Message: {await get_last_message(saved_chat_id)}'
    else:
        response = 'No target chat ID set.'
    await event.respond(response)

async def get_last_message(chat_id):
    try:
        async for message in client.iter_messages(int(chat_id), limit=1):
            return message.text if message.text else "Null"
    except Exception as e:
        return "Error: " + str(e)

@client.on(events.NewMessage(pattern='/stop'))
async def stop_typing(event):
    if str(event.sender_id) != owner_id:
        return
    global fake_typing_task
    if fake_typing_task:
        fake_typing_task.cancel()
        await event.respond('Fake typing stopped.')
    else:
        await event.respond('No fake typing task running.')

@client.on(events.NewMessage(pattern='/restart'))
async def restart(event):
    if str(event.sender_id) != owner_id:
        return
    await event.respond('Restarting bot...')
    os.execv(__file__, [__file__])

@client.on(events.NewMessage(pattern='/readall'))
async def read_all_messages(event):
    if str(event.sender_id) != owner_id:
        return
    await event.respond('Reading all messages...')
    async for message in client.iter_messages(target_chat_id):
        with open('msg.txt', 'a') as file:
            file.write(message.text + '\n')

@client.on(events.NewMessage(pattern='/menu'))
async def show_menu(event):
    if str(event.sender_id) != owner_id:
        return
    menu_text = "Daftar Menu:\n"
    menu_text += "/fake_typing - Memulai fake typing\n"
    menu_text += "/setid [ID] - Set target chat ID\n"
    menu_text += "/status - Menampilkan status bot\n"
    menu_text += "/stop - Menghentikan fake typing\n"
    menu_text += "/restart - Me-restart bot\n"
    menu_text += "/readall - Membaca semua pesan\n"
    menu_text += "/top - Menampilkan grup dengan pesan terbanyak\n"
    menu_text += "/Ping - Untuk Mengecek Kecepatan Respon\n"
    menu_text += "/speedtest - Untuk mengecek kecepatan internet\n"
    await event.respond(menu_text)

@client.on(events.NewMessage(pattern='/top'))
async def top_groups(event):
    if str(event.sender_id) != owner_id:
        return
    await event.respond('Fetching top 20 groups...')
    global unread_messages
    unread_messages = {}
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            unread_count = dialog.unread_count
            if unread_count > 0:
                unread_messages[dialog.id] = unread_count
    sorted_groups = sorted(unread_messages.items(), key=lambda x: x[1], reverse=True)[:20]
    top_groups_text = 'Top 20 groups with most unread messages:\n'
    for group_id, count in sorted_groups:
        chat = await client.get_entity(group_id)
        top_groups_text += f'{chat.title}: {count} unread messages\n'
    await event.respond(top_groups_text)

with open('owner.txt', 'w') as file:
    file.write(owner_id)
    
@client.on(events.NewMessage(pattern='/ping'))
async def ping(event):
    if str(event.sender_id) != owner_id:
        return
    start_time = time.time()
    await event.respond('Wait!')
    end_time = time.time()
    response_time = end_time - start_time
    await event.respond(f'Bot response time: {response_time:.2f} seconds')
    
@client.on(events.NewMessage(pattern='/speedtest'))
async def speed_test(event):
    if str(event.sender_id) != owner_id:
        return
    await event.respond('Running speed test...')
    st = speedtest.Speedtest()
    st.get_best_server()
    download_speed = st.download() / 1_000_000  # Convert to Mbps
    upload_speed = st.upload() / 1_000_000  # Convert to Mbps
    ping = st.results.ping
    server_info = st.results.server
    client_info = st.results.client
    await event.respond(f'Download speed: {download_speed:.2f} Mbps\nUpload speed: {upload_speed:.2f} Mbps\nPing: {ping} ms')
    await event.respond(f'Server Info:\n{server_info}')
    await event.respond(f'Client Info:\n{client_info}')
    
async def update_zall_name():
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    while True:
        current_time = datetime.datetime.now(jakarta_tz).strftime("%H:%M:%S WIB")
        try:
            await client(UpdateProfileRequest(
                first_name=f'Zall: {current_time}'
            ))
            await asyncio.sleep(25)
        except Exception as e:
            print(f'Error updating name: {e}')
            await asyncio.sleep(25)
async def main():
    await client.start()
    await update_zall_name()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())

client.start()
client.run_until_disconnected()