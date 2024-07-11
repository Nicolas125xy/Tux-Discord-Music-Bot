import discord
from   discord.ext import commands
import yt_dlp
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

FFMPEG_OPTIONS = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True}

class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = []

    @commands.command()
    async def play(self, ctx, *, search):
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("Você não está conectado em um canal de voz!")
        if not ctx.voice_client:
            await voice_channel.connect()
        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                url = info['url']
                title = info['title']
                self.queue.append((url, title))
                await ctx.send(f'Adicionado a fila: {title}')
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    async def play_next(self, ctx):
        try: 
            if self.queue:
                url, title = self.queue.pop(0)
                source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
                ctx.voice_client.play(source, after=lambda _: self.client.loop.create_task(self.play_next(ctx)))
                await ctx.send(f'Tocando agora: {title}')
            elif not ctx.voice_client.is_playing():
                await ctx.send("Todas as músicas da fila foram reproduzidas!")
        except Exception as e:
            print(e)

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Pulando música ⏭")

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.queue.clear()
            await ctx.send("Desligando a música e limpando a fila...")

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("Música pausada ⏸")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("A música voltou a tocar! ▶")

    @commands.command()
    async def ajuda(self, ctx):
        embed = discord.Embed(
            title='Comandos Disponíveis:',
            description='Lista de comandos do bot:',
            color=discord.Color.blue()
        )
        embed.add_field(name='!play', value='Inicia a reprodução de música.', inline=False)
        embed.add_field(name='!pause', value='Pausa a reprodução atual.', inline=False)
        embed.add_field(name='!resume', value='Resume a reprodução de música pausada.', inline=False)
        embed.add_field(name='!skip', value='Pula a música atual.', inline=False)
        embed.add_field(name='!stop', value='Para a reprodução e limpa a fila.', inline=False)

        await ctx.send(embed=embed)
    

client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    print(f'Bot entrou como: {client.user}!')

@client.event
async def on_disconnect():
    print('Bot desconectado.')

@client.event
async def on_error(event, *args, **kwargs):
    print('Ocorreu um erro.')

async def main():
    await client.add_cog(MusicBot(client))
    await client.start('Your-Token') 

asyncio.run(main())