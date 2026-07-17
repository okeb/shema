# Express REST API starter
A REST API boilerplate for NodeJS to show the bible simply.

> Uses MongoDB as its database and Passport for authentication with (jwt).



**TABLE OF CONTENTS**
- [Express REST API starter](#express-rest-api-starter)
  - [Libraries and tools used](#libraries-and-tools-used)
  - [USE CASES](#use-cases)
    - [example 1: *Have a sequence of verses*](#example-1-have-a-sequence-of-verses)
    - [example 2: *Have only one verse*](#example-2-have-only-one-verse)
    - [example 3: *Have a whole book*](#example-3-have-a-whole-book)
    - [example 4: *To have all the books of the author*](#example-4-to-have-all-the-books-of-the-author)
  - [Accepted abbreviations](#accepted-abbreviations)


---
## Libraries and tools used
- [Express](https://expressjs.com/)
- [Mongodb](https://www.mongodb.com)
- [Passport](https://github.com/jaredhanson/passport)
- [JsonWebToken](https://github.com/auth0/node-jsonwebtoken)
- [Mongoose]()
- [SwaggerUI](https://github.com/scottie1984/swagger-ui-express)
- [Morgan](https://github.com/expressjs/morgan), [Helmet](https://github.com/helmetjs/helmet), [Cors](https://github.com/expressjs/cors)
- [Mocha](https://mochajs.org/#getting-started), [Chai](http://chaijs.com/api/), [Supertest](https://github.com/visionmedia/supertest)
- [Winston](https://github.com/winstonjs/winston)

## USE CASES
The API user is simple and can be summarised as follows:
https://www.shemaproject.org/bym/ `book_name` /[ `chapter`/ ] [ `start_verset` ] [ - `end_verset`]
**elements in square brackets are optional **.



### example 1: *Have a sequence of verses* 

**Genesis 1:3-10**
To display verses 3 to 7 of the book of Genesis, chapter 1, we call in GET the following url :
https://www.shemaproject.org/bym/genèse/1/3-7

```json
{
   "Ge. 1:3":{
      "livre":"Ge. ",
      "chapitre":"1",
      "verset":3,
      "value":"Elohîm dit : Que la lumière apparaisse ! Et la lumière apparut."
   },
   "Ge. 1:4":{
      "livre":"Ge. ",
      "chapitre":"1",
      "verset":4,
      "value":"Elohîm vit que la lumière était bonne, et Elohîm sépara la lumière de la ténèbre."
   },
   "Ge. 1:5":{
      "livre":"Ge. ",
      "chapitre":"1",
      "verset":5,
      "value":"Elohîm appela la lumière jour, et il appela la ténèbre nuit. Le soir vint, et le matin vint : un jour."
   },
   "Ge. 1:6":{
      "livre":"Ge. ",
      "chapitre":"1",
      "verset":6,
      "value":"Elohîm dit : Que le firmament apparaisse entre les eaux et qu'il sépare les eaux d'avec les eaux !"
   },
   "Ge. 1:7":{
      "livre":"Ge. ",
      "chapitre":"1",
      "verset":7,
      "value":"Elohîm fit le firmament et sépara les eaux qui sont au-dessous du firmament d’avec les eaux qui sont au-dessus du firmament. Il en fut ainsi."
   }
}
```


### example 2: *Have only one verse* 

**Revelation 3:5**
You can also display a single verse by using URLs like this:
https://www.shemaproject.org/bym/ap/3/5

```json
{
   "Ap. 3:5":{
      "livre":"Ap. ",
      "chapitre":"3",
      "verset":5,
      "value":"Celui qui remporte la victoire sera revêtu de vêtements blancs, et je n'effacerai jamais son nom du livre de vie, mais je confesserai son nom devant mon Père et devant ses anges."
   }
}
```


### example 3: *Have a whole book* 

**Romans 8**
If you want to display a whole chapter, it is with a URL without verse like this: https://www.shemaproject.org/bym/ `book_name` /[ `chapter`/ ] 

For our example, we will have this URL:
https://www.shemaproject.org/bym/romains/8


### example 4: *To have all the books of the author* 

**RMatthew 1:1 to Matthew 28:20**
You have the possibility to display all the books of an author without adding any chapter or verse.
In the style: https://www.shemaproject.org/bym/ `book_name` /
 To better illustrate, the URL https://www.shemaproject.org/bym/Matthieu/ will display the verses from **Matthew 1:1 to Matthew 28:20**



## Accepted abbreviations
Based on [the Yehowshuw`a Ha-Mashiyah Bible](https://www.bibledeyehoshouahamashiah.org/lire.html) the accepted abbreviations are as follows:

Ge., Ex., Lé., No., De., Jos., Jg., 1 S., 2 S., 1 R., 2 R., Es., Jé., Ez., Os., Joë., Am., Ab., Jon., Mi., Na., Ha., So., Ag., Za., Mal., Ps., Pr., Job, Ca., Ru., La., Ec., Est., Da., Esd., Né., 1 Ch., 2 Ch., Mt., Mc., Lu., Jn., Ac., Ja., Ga., 1 Th., 2 Th., 1 Co., 2 Co., Ro., Ep., Ph., Col., Phm., 1 Ti., Tit., 1 Pi., 2 Pi., 2 Ti., Jud., Hé., 1 Jn., 2 Jn., 3 Jn., Ap.

However, you can write the names of the books directly (without spaces), and it works.


