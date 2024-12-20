import sqlite3
import os
import sys
import uuid
import random

class Program:
    def __init__(self):
        self.decks_dir = None
        
        # Array of the decks can be used like d[0],[1],[2],[3]
        self.all_decks = []

        # Array of the cards can be used like crd[0],[1],[2],[3]
        self.all_cards = []

        # Array of all decks
        self.decks_model = []

        # Array of all decks
        # INFO: Every deck strores a seperate deck.cardmodel array where all cards of the deck are stored
        self.cards_model = []

        # Array of appoptions intendet to be used with method self.Appoptions()
        self.appoptions = ["/exit", "/dialog", "/newcard"]

    def CheckForValidDB(self, filename):
        # Check if the database file exists
        db_file = os.path.join(self.decks_dir, filename)
        if not os.path.isfile(db_file):
            print(f"Database file '{db_file}' does not exist.")
            return False

        # Check if the tables exist
        table_names = ["decks", "cards"]
        required_columns_map = {
            "decks": ["deck_id", "name", "icon"],
            "cards": ["deck_id", "front", "back", "card_id"]
        }

        for table_name in table_names:
            table_status = self.UseDB(f"PRAGMA table_info({table_name});", filename)

            if table_status is None:
                print(f"Error checking for table '{table_name}' existence.")
                return False

            if not table_status:
                print(f"Table '{table_name}' does not exist in the database.")
                return False

            required_columns = required_columns_map[table_name]
            actual_columns = {column[1]: True for column in table_status}

            # Check for missing columns
            missing_columns = [column for column in required_columns if column not in actual_columns]

            # Check for columns with all None values
            all_none_columns = []
            for column in required_columns:
                if column in actual_columns:
                    column_values = [row[actual_columns[column]] for row in table_status]
                    if all(value is None for value in column_values):
                        all_none_columns.append(column)

            if missing_columns or all_none_columns:
                if table_name == "cards" and ("card_id" in missing_columns or "card_id" in all_none_columns):
                    print("The 'card_id' column is missing or all values are None. Migration is possible.")
                    user_response = input("Would you like to migrate your database now? [Y|es]/[N|o]: ").strip().lower()
                    if user_response in ["yes", "y"]:
                        try:
                            # Attempt to add the card_id column or update existing rows
                            if self.UseDB("ALTER TABLE cards ADD COLUMN card_id TEXT;", filename):
                                if self.migrate_card_ids(filename):
                                    print("Migration was successful.")
                                else:
                                    print("Migration of card IDs failed.")
                                return True
                            else:
                                print("Failed to alter the cards table. Migration aborted.")
                        except sqlite3.Error as e:
                            print(f"Migration failed: {e}")
                        return True  # Proceed if migration was attempted
                else:
                    print(f"Your Database looks broken, please fix it for table '{table_name}'. Missing columns: {', '.join(missing_columns)}")
                    return False

        return True

    def migrate_card_ids(self, filename):
        self.all_cards = self.UseDB("SELECT * FROM cards;", filename)
        for crd in self.all_cards:
            if crd[3] is None:  # If card_id is None
                newcardid = self.GenUUID4("card")
                # Update the database with this new card_id
                self.UseDB("UPDATE cards SET card_id = ? WHERE deck_id = ? AND front = ?",
                            filename, (newcardid, crd[0], crd[1]))

        # Verify if card IDs were successfully updated
        if any(crd[3] is None for crd in self.all_cards):
            print("Error while migrating your database. Some card IDs are still None.")
            return False

        return True

    def GenUUID4(self, mode:str):
        isvaliduuid = False
        while isvaliduuid != True:
            candidate_id = uuid.uuid4().hex
            if mode == "card":
                # Check that this id does not exist in the existing cards
                if not any(existing_card[3] == candidate_id for existing_card in self.all_cards):
                        isvaliduuid = True
                        return candidate_id
            elif mode == "deck":
                decksarray = self.AvalibleDecks()
                # Check if the deck exists
                if not any(deck.deck_id == candidate_id for deck in decksarray):
                    isvaliduuid = True
                    return candidate_id

    def LoadDecks(self, filename):
        data_dir = os.path.join(os.getcwd(), 'data')
        self.decks_dir = data_dir

        if self.CheckForValidDB(filename) != True:
            print("There is a problem with your database pls fix it")
            sys.exit(1)

        # Clear Decks_model to insure no wired bugs
        self.decks_model = []
        self.cards_model = []

        # Creating a list of decks
        self.all_decks = self.UseDB("SELECT * FROM decks;", filename)

        # Creating a list of cards
        self.all_cards = self.UseDB("SELECT * FROM cards;", filename)

        # Loads every card in from the db into a Card cls to append it to the cards_model array
        for crd in self.all_cards:
                card = Card()
                card.deck_id = crd[0]
                card.front = crd[1]
                card.back = crd[2]
                card.card_id = crd[3]
                self.cards_model.append(card)

        # Loads every decl in from the db into a deck cls to append it to the deck_model array
        for d in self.all_decks:
            deck = Deck()
            deck.deck_id = d[0]
            deck.name = d[1]
            deck.icon = d[2]
            
            # To store a array of cards that are connected to the deck via the deckid
            for crdmdl in self.cards_model:
                if crdmdl.deck_id == deck.deck_id:
                    deck.cards_model.append(card)

            self.decks_model.append(deck)

    def UseDB(self, command, filename, parameters=None):
        conn = None
        try:
            conn = sqlite3.connect(os.path.join(self.decks_dir, filename))
            c = conn.cursor()  # create a cursor instance

            if parameters is not None:  # if parameters are passed for the execute command
                c.execute(command, parameters)
            else:
                c.execute(command)

            if 'SELECT' in command or 'PRAGMA' in command:  # if the command is a SELECT or PRAGMA, grab the data
                out = c.fetchall()
                return out
            else:
                conn.commit()  # save changes to the database
                return True  # Indicate success for non-SELECT commands
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return None  # Return None to indicate an error
        finally:
            if conn:
                conn.close()  # Ensure the connection is closed

    def GetFile(self):
        return "database.db"

    def Dialog(self):
        self.LoadDecks(self.GetFile())
        print("Thoughtcards-cmd")
        print("----------------")
        print("1. Show avalible decks")
        print("2. Enter deck via name")
        print("3. Manage decks")
        print("4. Change cards")
        print(f"You can use also all other option thoughtout the program: {self.appoptions}")
        print("----------------")

        isvalidnumber = False
        while isvalidnumber is False:
            userpickedoption = input("Please enter a number of the activity you want to do: ").strip()
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
            self.ManageDecks()

        elif userpickedoption == "4":
            self.ChangeCardsOfDeck()
        
        elif userpickedoption in self.appoptions:
            self.AppOptions(userpickedoption)

        self.BackToMainDialog()

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
            if deck.icon in [None, '']:
                deck.icon = "None"
            decksinmodel.append(deck)
        return decksinmodel
    
    def ShowAvalibleDecks(self, decksarray):
        if not decksarray:  # Check if the array is empty
            print("No decks in database")
            return  # Exit the method if there are no decks

        for deck in decksarray:
            if deck.icon is None:
                deck.icon = "No Image"
            print(f"Deck: {deck.name} - {deck.icon} - Number of cards: {len(deck.cards_model)}")

    def EnterDeck(self):
        decksarray = self.AvalibleDecks()
        decksarraylower = [d.name.lower() for d in decksarray]

        isvaliddeckname = False
        selected_deck = None

        # Prints Out the Avalible decks to enter
        print("---")
        self.ShowAvalibleDecks(decksarray)

        while isvaliddeckname != True:
            decknametoenter = input("Please input the name of the deck you want to enter: ").strip()
            if decknametoenter.lower() in self.appoptions:
                self.AppOptions(decknametoenter.lower())
            elif decknametoenter.lower() in decksarraylower:
                isvaliddeckname = True
                selected_deck = decksarray[decksarraylower.index(decknametoenter.lower())]
                # get selected_deck_id
                selected_deck_id = next(d.deck_id for d in decksarray if d.name.lower() == decknametoenter.lower())
            else:
                print(f"The deck: \"{decknametoenter}\" is not available.")

        for d in self.decks_model:
            if selected_deck_id == d.deck_id:
                if len(d.cards_model) == 0:
                    i = input("There are no cards avalible. Do you want to create a new one? [Y|es]/[N|o]: ").strip().lower()
                    if i in self.appoptions:
                        self.AppOptions(i)
                    elif i in ["yes", "y"]:
                        self.NewCard()
                    else:
                        self.BackToMainDialog()
                break


        shuffelmode = None
        availableshufflemodes = ["1", "forward", "2", "backward", "3", "random", self.appoptions]
        while shuffelmode not in availableshufflemodes:
            print("What shuffle mode do you want to use?")
            print("1. Forward")
            print("2. Backward")
            print("3. Random")
            userinput = input("Please enter your answer here: ").lower().strip()
            if userinput in self.appoptions:
                self.AppOptions(userinput)
            elif userinput not in availableshufflemodes:
                print("Not an available shuffle mode, please try again.")
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

    def BackToMainDialog(self):
        goback = input("Do you want to go back to the main dialog? [Y|es]/[N|o]: ").strip()
        if goback.lower() in ["yes", "y"]:
            self.Dialog()
        elif goback.lower() in self.appoptions:
            self.AppOptions()
        else:
            sys.exit(0)

    def ChangeCardsOfDeck(self):
        decksarray = self.AvalibleDecks()
        decksarraylower = [d.name.lower() for d in decksarray]

        allcrds = self.all_cards
        if not allcrds:
            i = input("There are no cards avalible. Do you want to create a new one? [Y|es]/[N|o]: ").strip()
            if i in self.appoptions:
                self.AppOptions(i)
            elif i.lower() in ["yes", "y"]:
                self.NewCard()
            else:
                self.BackToMainDialog()
        
        isvaliddeckname = False
        selected_stack = Deck()
        print("---")
        self.ShowAvalibleDecks(decksarray)

        print("You can also type in /free to access the cards without a deck or /all for all cards in the db")
        while not isvaliddeckname:
            decknametoenter = input("Please input the name of the card stack you want to enter: ").strip()
            if decknametoenter.lower() in self.appoptions:
                self.AppOptions(decknametoenter.lower())
            elif decknametoenter.lower() == "/free":
                freecrd = [crd for crd in self.cards_model if crd.deck_id in [None, "None", ""] ]
                if not freecrd:  # Check if freecrd is empty list
                    print("No cards without a deck")
                    return
                else:
                    isvaliddeckname = True
                    selected_stack.cards_model = freecrd
            elif decknametoenter.lower() == "/all":
                allcrds = self.cards_model
                if allcrds == None:  # Check if allcrds is empty list
                    print("No cards are available")
                    return
                else:
                    isvaliddeckname = True
                    selected_stack.cards_model = self.cards_model
            elif decknametoenter.lower() in decksarraylower:
                isvaliddeckname = True
                selected_stack.cards_model = decksarray[decksarraylower.index(decknametoenter.lower())]
            else:
                print(f"The deck: \"{decknametoenter}\" is not available.")
                return
        
        # Check if the selected deck has cards
        if not selected_stack.cards_model:
            print("The selected deck has no cards.")
            return  # Exit early if the deck is empty
                
        print("Here are your cards in xml format:")
        cardcounter = 0
        maxlen = max( # calculates the highes number of dashes in a deck
            max(len(f"Front: {self.format_card_text(card.front)}"), len(f"Back: {self.format_card_text(card.front)}")) 
            for card in selected_stack.cards_model
        )
        card_index = {}

        for card in selected_stack.cards_model:
            cardcounter += 1                
            title = f"Card {cardcounter}"

            self.RenderCard(card, title, True, maxlen)  # passes the card of a deck, renders them out as multiple
        if card.card_id is not None:
            card_index[cardcounter] = card.card_id
        else:
            print(f"Warning: Card {cardcounter} has no ID")

        cardtoeditisvalid = False
        cardtoedit = None
        while not cardtoeditisvalid:
            cardtoedit = input("Please enter the number of the card you want to edit: ").strip()
            if cardtoedit in self.appoptions:
                self.AppOptions(cardtoedit)
            elif cardtoedit.isnumeric():
                cardtoeditisvalid = True
            else:
                print("Input is not a number")

        # Get safely the card ID
        card_number = int(cardtoedit)
        if card_number not in card_index:
            print("Card number not found.")
            return  # Exit early if the card index is invalid

        # Gets the card.card_id from the card index
        selected_card_id = card_index[card_number]
        # Gets the exact card via the now known card_id
        selected_card = next((card for card in selected_stack.cards_model if card.card_id == selected_card_id), None)
        
        if not selected_card:
            print("Card not found.")
            return  # Exit early if the selected card is invalid

        # Render the card to be edited
        self.RenderCard(selected_card, "Card to Edit", False, None)
        self.EditCard(selected_card, None)

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
        self.EditCard(newcard, "3")  # Start editing the new card
        if newcard.deck_id is None:
            i = input("Do you want to add it to a deck? [Y|es]/[N|o]: ").lower().strip()
            deck_to_add = Deck()
            ioption = None
            if i in self.appoptions:
                self.AppOptions(i)
            elif i in ["yes", "y"]:
                ioption = "y"
                # Allow the user to select a deck to add the new card
                decksarray = self.AvalibleDecks()
                self.ShowAvalibleDecks(decksarray)
                decksarraylower = [d.name.lower() for d in decksarray]
                isvaliddeckname = False
                while not isvaliddeckname:
                    userdecknametoaddto = input("Please enter a valid deck name you want to add your new card to: ").strip()
                    if userdecknametoaddto.lower() in decksarraylower:
                        deck_to_add = decksarray[decksarraylower.index(userdecknametoaddto.lower())]
                        deck_to_add.cards_model.append(newcard)  # Add the new card to the selected deck
                        isvaliddeckname = True
                    elif userdecknametoaddto.lower() in self.appoptions:
                        self.AppOptions(userdecknametoaddto.lower())
                    else:
                        print("The entered deck name is not valid. Please try again.")
            else:
                ioption = "n"
                deck_to_add.deck_id = "None"
            # Update the database; here you need to add a more robust way to store the card in the DB
            if not self.UseDB("INSERT INTO cards (deck_id, front, back) VALUES (?, ?, ?)", filename, (deck_to_add.deck_id, newcard.front, newcard.back)):
                print("Error while inserting into database")
            if ioption == "y":
                print(f"New card added to deck '{deck_to_add.name}' successfully.")
                
        else:
            print("Error: 212")
            self.Dialog()  # Returns to the main dialog
                
        self.BackToMainDialog()

    def EditCard(self, selected_card, userinputoption = None):
        validoption = False
        IsNewCard = True
        while validoption != True:
            if userinputoption is None:
                IsNewCard = False
                print("What do you want to do with this card?")
                print("1. Edit front")
                print("2. Edit back")
                print("3. Edit both")
                print("4. Delete card")
                print("5. Add to deck")
                userinputoption = input("Please enter the number of the option you want to execute: ").strip()
            possibleoptions = ["1", "2", "3", "4", "5", self.appoptions]
            if userinputoption not in possibleoptions:
                print("Invalid option, try again.")
            else:
                validoption = True

        if userinputoption == "1":
            updated_card = self.EditSiteOfCard(selected_card, "front", IsNewCard)
            return updated_card

        elif userinputoption == "2":
            updated_card = self.EditSiteOfCard(selected_card, "back", IsNewCard)
            return updated_card

        elif userinputoption == "3":
            updated_card = self.EditSiteOfCard(selected_card, "both", IsNewCard)
            return updated_card

        elif userinputoption == "4":
            self.DeleteCard(selected_card)

        elif userinputoption == "5":
            print("---")
            self.Addtodeck(selected_card)


        elif userinputoption in self.appoptions:
            self.AppOptions(userinputoption)

    def Addtodeck(self, selected_card):
        decksarray = self.AvalibleDecks()
        self.ShowAvalibleDecks(decksarray)
        decksarraylower = [d.name.lower() for d in decksarray]
        isvaliddeckname = False

        while not isvaliddeckname:
            userdecknametoaddto = input("Please enter a valid deck name you want to add your new card to: ").strip()
            
            if userdecknametoaddto.lower() in decksarraylower:
                isvaliddeckname = True
                
                # Find deck id for the selected deck
                updated_deck_id = next(d.deck_id for d in decksarray if d.name.lower() == userdecknametoaddto.lower())

                # Create new car based on selected card
                new_card_id = self.GenUUID4("card")  # Generate a new unique card ID
                self.UseDB("INSERT INTO cards (deck_id, front, back, card_id) VALUES (?, ?, ?, ?)", 
                        self.GetFile(), 
                        (updated_deck_id, selected_card.front, selected_card.back, new_card_id))
                
                print(f"Successfully added a new card to deck '{userdecknametoaddto}' with the front: '{selected_card.front}' and back: '{selected_card.back}'.")
            else:
                print("The entered deck name is not valid. Please try again.")

    def EditSiteOfCard(self, selected_card, side, IsNewCard):
        filename = self.GetFile()
        
        if side in ["front", "back"]:
            updated_card = self.EditSingle(selected_card, side, IsNewCard)
            # Use the deck_id column in your update query
            command = "UPDATE cards SET front = ?, back = ? WHERE card_id = ?"  

            if side == "front":
                self.UseDB(command, filename, (updated_card.front, selected_card.back, selected_card.card_id))  # Use deck_id
            elif side == "back":
                self.UseDB(command, filename, (selected_card.front, updated_card.back, selected_card.card_id))
            
            return updated_card
        else:
            updated_card_front = self.EditSingle(selected_card, "front", IsNewCard)
            updated_card_back = self.EditSingle(selected_card, "back", IsNewCard)
            command = "UPDATE cards SET front = ?, back = ? WHERE card_id = ?"
            
            # Update the database based on both sides
            self.UseDB(command, filename, (updated_card_front.front, updated_card_back.back, selected_card.card_id))
            
            return updated_card_back  # Or return the appropriate updated card

    def EditSingle(self, selected_card, side, IsNewCard:bool):
        print("Use <br> to input \"↵\"")
        if not IsNewCard:
            inputoption = f"Please input your new version of the {side} side: "
        else:
            inputoption = f"Please input your {side} side: "
        useredit = input(inputoption)
        if not IsNewCard:
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

    def format_card_text(self,text): # a very basic fn to convert \n's to <br> for a more clear view on the cli
        return text.replace('\n', '<br>')
    
    def DeleteCard(self, cardtodelete):
        if isinstance(cardtodelete, Card):

            self.RenderCard(cardtodelete, "Card To Delete", False, None)

            print("Are you sure you want to delete this card?")
            areyousure = input("THIS CHANGE IS IRREVERSIBLE [Yes]/[N|o]: ").lower().strip()
            if areyousure == "yes":
                command = "DELETE FROM cards WHERE card_id = ?"
                parameters = (cardtodelete.card_id,)  # Ensure this is a one-item tuple
                filename = self.GetFile()
                success = self.UseDB(command, filename, parameters)  # Execute the command
                if success:
                    print("Card deleted successfully.")
                else:
                    print("Failed to delete the card.")
                return
        else:
            print("Error: cardtodelete is not a card")
            return

    def ManageDecks(self):
        print("----------------")
        print("1. Create new Deck")
        print("2. Rename Deck")
        print("3. Delete Deck")
        print("----------------")
        isvalidinput = False
        while not isvalidinput:
            userinput = input("Please enter a number of the activity you want to do: ").strip()
            if userinput in self.appoptions:
                self.AppOptions(userinput)
                isvalidinput = True
            elif userinput in ["1", "2", "3"]:
                isvalidinput = True
            if userinput == "1":
                self.modifyDeck("new")
            elif userinput == "2":
                self.modifyDeck("rename")
            elif userinput == "3":
                self.modifyDeck("delete")

    def modifyDeck(self, option):
        filename = self.GetFile()
        decksarray = self.AvalibleDecks()
        decksarraylower = [d.name.lower() for d in decksarray]
        if option not in ["new", "rename", "delete"]:
            print("Invalid option in modifyDeck")
            return
        new_deck_id = None
        if option == "new":
            new_deck_id = self.GenUUID4("deck")
            newdeckquestion = "Please enter the deckname of the new deck: "
    
        elif option in ["rename", "delete"]:
            selected_deck = None
            self.ShowAvalibleDecks(decksarray)
            while not selected_deck:
                userDecktorename = input(f"Please enter the deckname of the deck you want to {option}: ").strip()
                if userDecktorename in self.appoptions:
                    self.AppOptions(userDecktorename)
                elif userDecktorename.lower() not in decksarraylower:
                    print("Deck not found please try again")
                else:
                    selected_deck = True
            if option == "rename":
                newdeckquestion = "Please enter the future name of your deck that you want to rename: "
        
        if option in ["new", "rename"]:
            isvaliddeckname = None
            while not isvaliddeckname:
                newuserdeckname = input(newdeckquestion).strip()
                if newuserdeckname in self.appoptions:
                    self.AppOptions(newuserdeckname)
                elif newuserdeckname.lower() in decksarraylower:
                    print("Deskname is already taken")
                else:
                    isvaliddeckname = True

                AddIcon = input("Do you want to add an Icon? [Y|es]/[N|o]: ").strip().lower()
                UserIcon = None
                if AddIcon in self.appoptions:
                    self.AppOptions(AddIcon)

                elif AddIcon in ["yes", "y"]:
                    while not UserIcon:
                        UserIcon = input("Please insert your icon (for now only emojis) here: ").strip()
                        if UserIcon in self.appoptions:
                            self.AppOptions(UserIcon)

        if option == "new":
            if self.UseDB("INSERT INTO decks (deck_id, name, icon) VALUES (?, ?, ?)", filename, (new_deck_id, newuserdeckname, UserIcon)):
                print(f"New deck '{newuserdeckname}' created successfully.")
            else:
                print(f"New deck '{newuserdeckname}' creation faild.")

        elif option == "rename":
            deck_idofthetorenamed = next(d.deck_id for d in decksarray if d.name.lower() == userDecktorename.lower())
            if self.UseDB("UPDATE decks SET name = ? WHERE deck_id = ?", filename, (newuserdeckname, deck_idofthetorenamed)):
                print(f"Renaming of deck form: '{userDecktorename}' to: '{newuserdeckname}' was successful")
            else:
                print(f"Renaming of deck form: '{userDecktorename}' to: '{newuserdeckname}' was not successful")
        
        elif option == "delete":
            print("Are you shure you want to continue? This will delete the deck")
            areyousure = input("Please type in: 'I AM SURE I WANT TO DELTETE THIS DECK': ").strip()
            if areyousure == "I AM SURE I WANT TO DELTETE THIS DECK":
                #get deckid 
                deck_idofthetodelte = next(d.deck_id for d in decksarray if d.name.lower() == userDecktorename.lower())
                hascards = True
                for d in self.decks_model:
                    if deck_idofthetodelte == d.deck_id:
                        if len(d.cards_model) == 0:
                            hascards = False
                if not self.UseDB("DELETE FROM decks WHERE deck_id = ?", filename, (deck_idofthetodelte,)):
                    print(f"Error while removeing the deck: '{userDecktorename}'")
                    return
                else:
                    print(f"Removed successfully the deck: '{userDecktorename}'")
                    if hascards:
                        if not self.UseDB("UPDATE cards SET deck_id = ? WHERE deck_id = ? ", filename, (None, deck_idofthetodelte)):
                            print(f"Error while updateing the decks cards: '{userDecktorename}'")
                        else:
                            print(f"The cards of '{userDecktorename}' are now avalible in free cards")
                
class Deck:
    def __init__(self):
        self.deck_id = None
        self.name = None
        self.icon = None
        self.cards_model = []

class Card:
    def __init__(self):
        self.deck_id = None
        self.front = None
        self.back = None
        self.card_id = None

if __name__ == '__main__':
    program = Program()
    program.Dialog()
