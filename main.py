import sqlite3
import os
import sys
import uuid
import random

class Program:
    def __init__(self):
        self.decks_dir = None
        self.decks = []
        self.all_cards = []
        self.decks_model = []
        self.appoptions = ["/exit", "/dialog", "/newcard"]

    def LoadDecks(self, filename):
        data_dir = os.path.join(os.getcwd(), 'data')
        self.decks_dir = data_dir

        # create a list of decks
        self.decks = self.UseDB("SELECT * FROM decks;", filename)  # holds the id, name and icon of all decks

        # eine Liste der cards erstellen
        self.all_cards = self.UseDB("SELECT * FROM cards;", filename)  # holds id, front and back of all cards

        for d in self.decks:
            deck = Deck()
            deck.id = d[0]
            deck.name = d[1]
            deck.icon = d[2]
            for crd in self.all_cards:
                if crd[0] == deck.id:
                    card = Card()
                    card.id = crd[0]
                    card.front = crd[1]
                    card.back = crd[2]
                    deck.cards_model.append(card)
            self.decks_model.append(deck)

    def UseDB(self, command, filename, parameters=None):
        conn = sqlite3.connect(os.path.join(self.decks_dir, filename))
        c = conn.cursor()  # create a cursor instance

        if parameters is not None:  # if parameter is passed on execute command
            c.execute(command, parameters)
        else:
            c.execute(command)

        if 'SELECT' in command:  # if the command is a SELECT grab the data
            out = c.fetchall()
            conn.close()   # close connection
            return out
        else:
            conn.commit()   # safe changes on db
            conn.close()   # close connection

    def GetFile(self):
        return "database.db"
    def Dialog(self):
        self.LoadDecks(self.GetFile())
        print("Thoughtcards-cmd")
        print("----------------")
        print("1. Show avalible decks")
        print("2. Enter deck via name")
        print("3. Create a new deck")
        print("4. Change cards of a deck")
        print(f"You can use also all other option thoughtout the program: {self.appoptions}")
        print("----------------")

        isvalidnumber = False
        while isvalidnumber is False:
            userpickedoption = input("Please enter a Number of the activity you want to do: ").strip()
            if userpickedoption in ["1", "2", "3", "4", self.appoptions]:
                isvalidnumber = True

        if userpickedoption == "1":
            # This will print out the avalible decks in the db
            print("---")
            decksarray = self.AvalibleDecks()
            self.ShowAvalibleDecks(decksarray)
            self.BackToMainDialog()

        elif userpickedoption == "2":
            self.EnterDeck()

        elif userpickedoption == "3":
            self.CreateDeck()

        elif userpickedoption == "4":
            self.ChangeCardsOfDeck()
        
        elif userpickedoption in self.appoptions:
            self.AppOptions(userpickedoption)
 
    def AppOptions(self, optionarg:str):
        # This method is meant as a universal navigation tool
        if optionarg not in self.appoptions:
            return False # if false it isn't a appoption -> wrong input -> return if in a loop
        if optionarg == "/exit":
            print("Existing programm")
            sys.exit(0)
        elif optionarg == "/dialog":
            self.Dialog()
            return
        elif optionarg == "/newcard":
            self.NewCard()
            return
 
    def AvalibleDecks(self):
        decksinmodel = []
        for deck in self.decks_model:
            decksinmodel.append(deck)
        return decksinmodel
    
    def ShowAvalibleDecks(self, decksarray):
        for deck in decksarray:
            print(f"Deck: {deck.name} - {deck.icon}- Number of cards: {len(deck.cards_model)}")
            if not self.decks_model:
                print("No decks in database")

    def EnterDeck(self):
        decksarray = self.AvalibleDecks()
        decksarraylower = [d.name.lower() for d in decksarray]

        isvaliddeckname = False
        selected_deck = None

        # Prints Out the Avalible decks to enter
        print("---")
        decksarray = self.AvalibleDecks()
        self.ShowAvalibleDecks(decksarray)

        while isvaliddeckname != True:
            decknametoenter = input("Please input the name of the deck you want to enter: ").strip()
            if decknametoenter.lower() in self.appoptions:
                self.AppOptions(decknametoenter.lower())
            elif decknametoenter.lower() in decksarraylower:
                isvaliddeckname = True
                selected_deck = decksarray[decksarraylower.index(decknametoenter.lower())]
            else:
                print(f"The deck: \"{decknametoenter}\" is not available.")

        shuffelmode = None
        availableshufflemodes = ["1", "forward", "2", "backward", "3", "random", self.appoptions]
        while shuffelmode not in availableshufflemodes:
            print("What shuffle mode do you want to use?")
            print("1. Forward")
            print("2. Backward")
            print("3. Random")
            userinput = input("Please enter your answer here: ").lower().strip()
            if userinput not in availableshufflemodes:
                print("Not an available shuffle mode, please try again.")
            elif userinput in self.appoptions:
                self.AppOptions(userinput)
            else:
                shuffelmode = userinput

        print(f"You selected the deck: \"{selected_deck.name}\"")
        if shuffelmode in ["1", "forward"]:
            selected_deck.cards_model.sort(key=lambda card: card.front)  # Sort by front
            print(f"You selected shuffle mode: \"Forward\"")
        elif shuffelmode in ["2", "backward"]:
            selected_deck.cards_model.sort(key=lambda card: card.front, reverse=True)  # Sort by front in reverse
            print(f"You selected shuffle mode: \"Backward\"")
        else:
            random.shuffle(selected_deck.cards_model)
            print(f"You selected shuffle mode: \"Random\"")

        print("Here are your cards:")
        for card in selected_deck.cards_model:
            i  = input(f"Front: {card.front}\n")
            """if i not in self.appoptions:
                self.AppOptions(i)
            else:"""
            if i is not None:
                print(f"Back: {card.back}")
                print(f"+---------------+")

        print("That where all cards in your deck.")
        self.BackToMainDialog()

    def BackToMainDialog(self):
        goback = input("Do you want to go back to the main dialog? [Y|es]/[N|o]").strip()
        if goback.lower() in ["yes", "y"]:
            self.Dialog()
        elif goback.lower() in self.appoptions:
            self.AppOptions()
        else:
            sys.exit(0)
    
    def ChangeCardsOfDeck(self):
        decksarray = self.AvalibleDecks()
        decksarraylower = [d.name.lower() for d in decksarray]

        print("---")
        self.ShowAvalibleDecks(decksarray)

        decknametoenter = input("Please input the name of the deck you want to enter: ").strip()
        isvaliddeckname = False
        selected_deck = None

        while not isvaliddeckname:
            if decknametoenter.lower() in decksarraylower:
                isvaliddeckname = True
                selected_deck = decksarray[decksarraylower.index(decknametoenter.lower())]
            else:
                print(f"The deck: \"{decknametoenter}\" is not available.")
                decknametoenter = input("Please input the name of the deck you want to enter: ").strip()
            
        print("Here are your cards in xml format:")
        cardcounter:int = 0
        maxlen = max( # calculates the highes number of dashes in a deck
            max(len(f"Front: {self.format_card_text(card.front)}"), len(f"Back: {self.format_card_text(card.front)}")) 
            for card in selected_deck.cards_model
        )
        card_index = {}

        for card in selected_deck.cards_model:
            cardcounter += 1                
            title = f"Card {cardcounter}"

            self.RenderCard(card, title, True, maxlen) # passes the card of a deck, render them out as multiple
            card_index[cardcounter] = card.id

        cardtoeditisvalid = False
        cardtoedit = None
        while not cardtoeditisvalid:
            cardtoedit = input("Please enter the number of the card you want to edit: ").strip()
            if cardtoedit.isnumeric():
                cardtoeditisvalid = True
            else:
                print("Input is not a number")

        # Get safely the card ID
        if not int(cardtoedit) in card_index:
            print("Card number not found.")
            return  # Exit early if the card index is invalid

        selected_card_id = card_index[int(cardtoedit)]
        selected_card = next((card for card in selected_deck.cards_model if card.id == selected_card_id), None)
        
        if not selected_card:
            print("Card not found.")
            return  # Exit early if the selected card is invalid

        # Render the card to be edited
        self.RenderCard(selected_card, "Card to Delete", False, None)
        self.EditCard(selected_card, False, None)

    
    def RenderCard(self, card, title:str, RenderMultipleCards:bool, maxlen:int):
        if not RenderMultipleCards or maxlen is None:
            # Calculate maxlen correctly based on the current card
            maxlen = max(len(f"Front: {self.format_card_text(card.front)}"),
                        len(f"Back: {self.format_card_text(card.back)}"))

        # Now ensure maxlen has a value before using it
        total_length = maxlen + len(title) + 4  # +4 for the "+ " and " +"
        left_dashes = (total_length - len(title) - 2) // 2  # Calculate dashes accordingly
        right_dashes = total_length - len(title) - left_dashes - 2  # Remaining dashes

        # first line with dashes
        print(f"+{'-' * left_dashes} {title} {'-' * right_dashes}+")
        print(f"Front: {self.format_card_text(card.front)}")
        print(f"Back: {self.format_card_text(card.back)}")
        print(f"+{'-' * (total_length)}+")  # last line with same number of dashes 

    def NewCard(self):
        newcard = Card()  # Initialize a new card
        filename = self.GetFile()
        self.EditCard(newcard, True, None)  # Start editing the new card
        if newcard.deck_id is None:
            i = input("Do you want to add it to a deck? Else it will be dropped [Y|es]/[N|o] ").lower().strip()
            if i in self.appoptions:
                self.AppOptions(i)
            elif i in ["yes", "y"]:
                # Allow the user to select a deck to add the new card
                decksarray = self.AvalibleDecks()
                self.ShowAvalibleDecks(decksarray)
                decksarraylower = [d.name.lower() for d in decksarray]
                isvaliddeckname = False
                while not isvaliddeckname:
                    userdecknametoaddto = input("Please enter a valid deck name you want to add your new card to: ").strip()
                    if userdecknametoaddto.lower() in decksarraylower:
                        isvaliddeckname = True
                        deck_to_add = decksarray[decksarraylower.index(userdecknametoaddto.lower())]
                        deck_to_add.cards_model.append(newcard)  # Add the new card to the selected deck
                        # Update the database; here you need to add a more robust way to store the card in the DB
                        self.UseDB("INSERT INTO cards (deck_id, front, back) VALUES (?, ?, ?)", filename, (deck_to_add.id, newcard.front, newcard.back))
                        print(f"New card added to deck '{deck_to_add.name}' successfully.")
                    else:
                        print("The entered deck name is not valid. Please try again.")
            else:
                self.Dialog()  # Returns to the main dialog
                
        self.BackToMainDialog()

    def EditCard(self, selected_card, IsNewCard:bool, userinputoption):
        validoption:bool = False
        while validoption != True:
            print("What do you want to do with this card?")
            print("1. Edit front")
            print("2. Edit back")
            print("3. Edit both")
            print("4. Delete card")
            if IsNewCard:
                print("5. Add to deck")
            userinputoption = input("Please enter the number of the option you want to execute: ").strip()
            possibleoptions = ["1", "2", "3", "4", self.appoptions]
            if IsNewCard:
                possibleoptions.append("5")
            if userinputoption not in possibleoptions:
                print("Invalid option try again")
            else:
                validoption = True
        if userinputoption == "1":
            updated_card = self.EditSiteOfCard(selected_card, "front")
            
            return updated_card
        elif userinputoption == "2":
            updated_card = self.EditSiteOfCard(selected_card, "back")
            return updated_card
        elif userinputoption == "3":
            updated_card = self.EditSiteOfCard(selected_card, "both")
            return updated_card
        elif userinputoption == "4":
            self.RenderCard(selected_card, "Card to Delete", False, None) ######## Working here
            print("Are you shure you want to delete this card?")
            areyousure = input("THIS CHANGE IS IRREVERSIBLE [Y|es]/[N|o]: ").lower().strip()
            if areyousure in ["yes", "y"]:
                selected_card
                    
            command = '''DELETE FROM cards WHERE deck_id = ? AND front = ? AND back = ?'''
            parameters = (selected_card.deck_id, selected_card.front, selected_card.back)
            filename = self.GetFile()
            self.UseDB(command, filename, parameters)

        elif userinputoption == "5":
            print("---")
            decksarray = self.AvalibleDecks()
            self.ShowAvalibleDecks(decksarray)
            decksarraylower = [d.name.lower() for d in decksarray]
            isvaliddeckname = False
            while isvaliddeckname != True:
                userdecknametoaddto = input("Please enter a valid deckname you want to your new card to: ")
                if userdecknametoaddto in decksarraylower:
                    isvaliddeckname = True
                    updated_card = selected_card
                    updated_card.deck_id = userdecknametoaddto
                    self.UseDB(updated_card,self.GetFile())
                    self.UseDB("INSERT INTO cards (deck_id, front, back) VALUES (?, ?, ?)", filename, (updated_card.deck_id, updated_card.front, updated_card.back))
                else:
                    print("The entered deckname is not a deck. Please try again")
        elif userinputoption in self.appoptions:
            self.AppOptions(userinputoption)

    def EditSiteOfCard(self, selected_card, side):
        filename = self.GetFile()
        
        if side in ["front", "back"]:
            updated_card = self.EditSingle(selected_card, side)
            # Use the deck_id column in your update query
            command = "UPDATE cards SET front = ?, back = ? WHERE deck_id = ?"  

            if side == "front":
                self.UseDB(command, filename, (updated_card.front, selected_card.back, selected_card.deck_id))  # Use deck_id
            elif side == "back":
                self.UseDB(command, filename, (selected_card.front, updated_card.back, selected_card.deck_id))
            
            return updated_card
        else:
            updated_card_front = self.EditSingle(selected_card, "front")
            updated_card_back = self.EditSingle(selected_card, "back")
            command = "UPDATE cards SET front = ?, back = ? WHERE deck_id = ?"
            
            # Update the database based on both sides
            self.UseDB(command, filename, (updated_card_front.front, updated_card_back.back, selected_card.deck_id))
            
            return updated_card_back  # Or return the appropriate updated card

    def EditSingle(self, selected_card, side):
        print("Use <br> to input \"↵\"")
        useredit = input(f"Please input your new version of the {side} side: ")
        print(f"Are you sure you want to update the {side} side of your card to: ")
        print(useredit)
        areyousure = input("THIS CHANGE IS IRREVERSIBLE [Y|es]/[N|o] ")
        if areyousure.lower() in ["y", "yes"]:
            if side == "front":
                selected_card.front = useredit  # Update front side
            elif side == "back":
                selected_card.back = useredit  # Update back side
            
            print(f"Card updated: Front - {selected_card.front}, Back - {selected_card.back}")
            return selected_card  # return changes

        return selected_card  # retrun the og card if no changes where made

    def format_card_text(self,text):
        return text.replace('\n', '<br>')

    def CreateDeck(self):
        filename = self.GetFile()
        self.LoadDecks(filename)
        decksarray = self.AvalibleDecks()
        DeckIDExistsAlready = False
        while not DeckIDExistsAlready:
            deck_id = uuid.uuid4().hex
            if not any(deck.id == deck_id for deck in decksarray):  # Check if the deck exists
                DeckIDExistsAlready = True
        deck_name = input("Please enter your deck name here: ").strip()
        if deck_name in self.appoption:
            self.AppOptions(deck_name)
        AddedIconPassed = False
        UserIcon = None
        AddIcon = input("Do you want to add an Icon? [Y|es]/[N|o]: ").strip().lower()
        if AddIcon in self.appoption:
            self.AppOptions(AddIcon)
        elif AddIcon in ["y", "yes"]:
            UserIconExists = False
            while not UserIconExists:
                UserIcon = input("Please insert your icon (for now only emojis) here: ")
                UserIconExists = UserIcon is not None
            AddedIconPassed = True
        else:
            AddedIconPassed = True

        if AddedIconPassed:
            self.UseDB("INSERT INTO decks (deck_id, name, icon) VALUES (?, ?, ?)", filename, (deck_id, deck_name, UserIcon))
            print(f"New deck '{deck_name}' created successfully.")
        else:
            print("Error 213")

class Deck:
    def __init__(self):
        self.id = None
        self.name = None
        self.icon = None
        self.cards_model = []

class Card:
    def __init__(self):
        self.deck_id = None
        self.front = None
        self.back = None

if __name__ == '__main__':
    program = Program()
    program.Dialog()
