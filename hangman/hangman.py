import discord
import os

from discord.ext import commands
from random import randint

from .utils.dataIO import dataIO
from .utils import checks


class Hangman:
    """Lets anyone play a game of hangman with custom phrases"""

    def __init__(self, bot):
        self.bot = bot
        self.path = "data/Fox-Cogs/hangman"
        self.file_path = "data/Fox-Cogs/hangman/hangman.json"
        self.answer_path = "data/hangman/hanganswers.txt"
        self.the_data = dataIO.load_json(self.file_path)
        self.winbool = False
        self.letters = "🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿"
        self._updateHanglist()

    def _updateHanglist(self):
        self.hanglist = (
            """>
               \_________
                |/        
                |              
                |                
                |                 
                |               
                |                   
                |\___                 
                """,

            """>
               \_________
                |/   |      
                |              
                |                
                |                 
                |               
                |                   
                |\___                 
                H""",

            """>
               \_________       
                |/   |              
                |   """+self.the_data["theface"]+"""
                |                         
                |                       
                |                         
                |                          
                |\___                       
                HA""",

            """>
               \________               
                |/   |                   
                |   """+self.the_data["theface"]+"""                   
                |    |                     
                |    |                    
                |                           
                |                            
                |\___                    
                HAN""",


            """>
               \_________             
                |/   |               
                |   """+self.the_data["theface"]+"""                    
                |   /|                     
                |     |                    
                |                        
                |                          
                |\___                          
                HANG""",


            """>
               \_________              
                |/   |                     
                |   """+self.the_data["theface"]+"""                      
                |   /|\                    
                |     |                       
                |                             
                |                            
                |\___                          
                HANGM""",



            """>
               \________                   
                |/   |                         
                |   """+self.the_data["theface"]+"""                       
                |   /|\                             
                |     |                          
                |   /                            
                |                                  
                |\___                              
                HANGMA""",


            """>
               \________
                |/   |     
                |   """+self.the_data["theface"]+"""     
                |   /|\           
                |     |        
                |   / \        
                |               
                |\___           
                HANGMAN""")
              
    def save_data(self):
        """Saves the json"""
        dataIO.save_json(self.file_path, self.the_data)
        
    @commands.group(aliases=['sethang'], pass_context=True)
    @checks.mod_or_permissions(administrator=True)
    async def hangset(self, ctx):
        """Adjust hangman settings"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)
            
    @hangset.command(pass_context=True)
    async def face(self, ctx, theface):
        message = ctx.message
        #Borrowing FlapJack's emoji validation (https://github.com/flapjax/FlapJack-Cogs/blob/master/smartreact/smartreact.py)
        if theface[:2] == "<:":
            theface = [r for server in self.bot.servers for r in server.emojis if r.id == theface.split(':')[2][:-1]][0]
        
        try:
            # Use the face as reaction to see if it's valid (THANKS FLAPJACK <3)
            await self.bot.add_reaction(message, theface)
            self.the_data["theface"] = str(theface)
            self.save_data()
            self._updateHanglist()
            await self.bot.say("Face has been updated!")

        except discord.errors.HTTPException:
            await self.bot.say("That's not an emoji I recognize.")
            
    @commands.command(aliases=['hang'], pass_context=True)
    async def hangman(self, ctx, guess: str=None):
        """Play a game of hangman against the bot!"""
        if guess is None:
            if self.the_data["running"]:
                await self.bot.say("Game of hangman is already running!\nEnter your guess!")
                self._printgame()
                """await self.bot.send_cmd_help(ctx)"""
            else:
                await self.bot.say("Starting a game of hangman!")
                self._startgame()
                await self._printgame()
        elif not self.the_data["running"]:
            await self.bot.say("Game of hangman is not yet running!\nStarting a game of hangman!")
            self._startgame()
            await self._printgame()
        else:    
            await self._guessletter(guess)
            
            if self.winbool:
                await self.bot.say("You Win!")
                self._stopgame()
                
            if self.the_data["hangman"] >= 7:
                await self.bot.say("You Lose!\nThe Answer was: **"+self.the_data["answer"]+"**")
                self._stopgame()
                
    def _startgame(self):
        """Starts a new game of hangman"""
        self.the_data["answer"] = self._getphrase().upper()
        self.the_data["hangman"] = 0
        self.the_data["guesses"] = []
        self.winbool = False
        self.the_data["running"] = True
        self.save_data()
        
    def _stopgame(self):
        """Stops the game in current state"""
        self.the_data["running"] = False
        self.save_data()
    
    def _getphrase(self):
        """Get a new phrase for the game and returns it"""
        phrasefile = open(self.answer_path, 'r')
        phrases = phrasefile.readlines()
        
        outphrase = ""
        while outphrase == "":
            outphrase = phrases[randint(0, len(phrases)-1)].partition(" (")[0]
#           outphrase = phrases[randint(0,10)].partition(" (")[0]
        return outphrase
   
    def _hideanswer(self):
        """Returns the obscured answer"""
        out_str = ""
        
        self.winbool = True
        for i in self.the_data["answer"]:
            if i == " " or i == "-":
                out_str += i*2
            elif i in self.the_data["guesses"] or i not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                out_str += "__"+i+"__ "
            else:
                out_str += "**\_** "
                self.winbool = False
                
        return out_str
        
    def _guesslist(self):
        """Returns the current letter list"""
        out_str = ""
        for i in self.the_data["guesses"]:
            out_str += str(i) + ","
        out_str = out_str[:-1]
        
        return out_str
        
    async def _guessletter(self, guess: chr=None):
        """Checks the guess on a letter and prints game if acceptable guess"""
        if not guess.upper() in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" or not len(guess) == 1:
            await self.bot.say("Invalid guess. Only A-Z is accepted")
            return

        if guess.upper() in self.the_data["guesses"]:
            await self.bot.say("Already guessed that! Try again")
            return

        if not guess.upper() in self.the_data["answer"]:
            self.the_data["hangman"] += 1
            
        self.the_data["guesses"].append(guess.upper())
        self.save_data()
        
        await self._printgame()
            
    async def _printgame(self):
        """Print the current state of game"""
        cSay = ("Guess this: " + str(self._hideanswer()) + "\n"
                + "Used Letters: " + str(self._guesslist()) + "\n"
                + self.hanglist[self.the_data["hangman"]])
        message = await self.bot.say(cSay)
        for x in range(len(self.letters)):
            if x not in [i for i,b in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ") if b in self._guesslist()]:
                await self.bot.add_reaction(message, self.letters[x])
        
    
def check_folders():
    if not os.path.exists("data/Fox-Cogs"):
        print("Creating data/Fox-Cogs folder...")
        os.makedirs("data/Fox-Cogs")

    if not os.path.exists("data/Fox-Cogs/hangman"):
        print("Creating data/Fox-Cogs/hangman folder...")
        os.makedirs("data/Fox-Cogs/hangman")

        
def check_files():
    if not dataIO.is_valid_json("data/Fox-Cogs/hangman/hangman.json"):
        dataIO.save_json("data/Fox-Cogs/hangman/hangman.json", {"running": False, "hangman": 0, "guesses": [], "theface": "<:never:336861463446814720>"})
    

def setup(bot):
    check_folders()
    check_files()
    if True:  # soupAvailable: No longer need Soup
        bot.add_cog(Hangman(bot))
    else:
        raise RuntimeError("You need to run `pip3 install beautifulsoup4`")
