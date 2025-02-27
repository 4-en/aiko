import spacy

nlp = spacy.load("en_core_web_sm")


text = """
Hans Eli Sebastian Fors (born 16 December 1990), known by the pseudonym Forsen, is a Swedish Twitch streamer who initially gained popularity for having competed in StarCraft II, but is best known for competing in Hearthstone and for streaming a variety of popular games. He is also known for his rowdy fanbase, who call themselves "Forsen Boys" or "Forsen Bajs" and have had a hand in popularizing a number of Internet memes. Since December 2018, Forsen has had over one million followers on Twitch, and as of June 2024, has more than 1.7 million followers.
Esports career
StarCraft II

In 2011, Forsen won first place in the E-Sport SM May Qualifier and was the runner-up in the E-Sport SM October Qualifier, earning a total of 3,500 Swedish krona ($382.50) and qualifying for the Swedish National Championships in StarCraft II. In 2012, Forsen garnered attention by advancing to the final group stage of the 2012 DreamHack Stockholm StarCraft II tournament.
Hearthstone

In Hearthstone, Forsen won his first tournament in the May 2015 HTC Invitational, and won a Play it Cool streaming marathon in October 2015, achieving the highest rank among the competitors after 24 hours of play. In 2015, Forsen was one of the top four Hearthstone streamers, streaming to up to 45,000 viewers on his live stream on Twitch. He was once known as one of the game's most skilled experts at the Miracle Rogue deck, having piloted it to achieve the highest rank in the game's ladder system on both the North American and European servers in June 2014. In 2017, after spending much of his Hearthstone career as a free agent, Forsen signed with American esports organization Cloud9 as a streamer."""

doc = nlp(text)

# print named entities in article
allowed_entities = {"PERSON", "ORG", "GPE", "NORP", "FAC", "LOC", "PRODUCT", "EVENT", "WORK_OF_ART", "LAW", "LANGUAGE"}

for ent in doc.ents:
    if ent.label_ in allowed_entities:
        print(ent.text, ent.label_)