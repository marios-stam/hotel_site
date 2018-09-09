import sqlite3
import re


def sql(text,*args):
    con = sqlite3.connect("hotel.db")
    con.isolation_level = None
    cur = con.cursor()
    cur.execute(text,args)
    result=cur.fetchall()
    con.close()
    return result

def load_available_rooms(form_dict):
    print("Dates",form_dict["Check-in"],"-",form_dict["Check-out"])
    query="""
            SELECT ROOMS.Room_ID,
                ROOM_TYPES.ADULT_CAPACITY,
                ROOM_TYPES.CHILDREN_CAPACITY,
                ROOM_TYPES.DESCRIPTION,
                ROOM_TYPES.Preview_Photo,
                Rooms."Wi-Fi",
                Rooms.SEA_VIEW,
                Rooms.BAR,
                Rooms.Cuisine
                
                FROM Rooms 
                INNER JOIN ROOM_TYPES ON Rooms.ROOM_TYPE_ID=ROOM_TYPES.ROOM_TYPE_ID


                WHERE Rooms.Room_ID NOT IN  
                
                (SELECT Rooms.Room_ID FROM Rooms  
                INNER JOIN RESERVATIONS ON RESERVATIONS.Room_ID=Rooms.Room_ID
                
                WHERE  
                    RESERVATIONS.[Check-in] 
                     BETWEEN ?  AND ?
                AND 
                    RESERVATIONS.[Check-OUT]    
                     BETWEEN ?  AND ?
                )
        """   
    
    rooms=sql(query,form_dict["Check-in"],form_dict["Check-out"],form_dict["Check-in"],form_dict["Check-out"])
    rooms=dictionarify(query,rooms)
    return rooms

def get_modal_details(room_id):
    query="""SELECT ROOM_TYPES.DESCRIPTION ,ROOM_TYPES.ADULT_CAPACITY ,ROOM_TYPES.CHILDREN_CAPACITY  ,Rooms."Wi-Fi",Rooms.SEA_VIEW,Rooms.BAR   FROM Rooms 
    INNER JOIN ROOM_TYPES ON Rooms.ROOM_TYPE_ID=ROOM_TYPES.ROOM_TYPE_ID
    WHERE Rooms.ROOM_ID=?"""
    details=sql(query,room_id)
    details=dictionarify(query,details)[0]
    for key,value in details.items():
        if value==1:
            details[key]="<i class='fa fa-check'></i>"
        elif value==0:
            details[key]='<i class="fa fa-times"></i>'
    photos=[]
    for i in sql("""SELECT Photo FROM Room_photos WHERE Room_ID=?""",room_id):
        photos.append(i[0])
    details.update({"Photos":photos})
    return details

def dictionarify(sql_query,sql_result):
    word_1="SELECT"   
    index_1 = re.search(r'\b(SELECT)\b', sql_query)
    word_2="FROM"   
    index_2 = re.search(r'\b(FROM)\b', sql_query)
    cols=sql_query[index_1.start()+len(word_1):index_2.start()]
    apotelesmata=[]
    cols=cols.split(',')
    columns=[]
    #=========================================================================================
    try:
        for i in cols:
            columns=columns+[ (i.split('.')[1]).strip() ]
    except:
        for i in cols:
            columns=columns+[ i.strip() ]
    #=========================================================================================
    for i in range(len(sql_result)):
        leksikaki={}
        for j in range(len(columns)):
            leksikaki.update({ columns[j].replace('"',"").replace("_"," "):sql_result[i][j]} )
        apotelesmata=apotelesmata+[leksikaki]
    return apotelesmata


def check_credentials(username,password):
    query="""SELECT EXISTS 
         (
        SELECT * FROM Customers WHERE Customers."e-mail"=? AND Customers.Password=?    
        ) 
        """
    return sql(query,username,password)[0][0]

def avaiability_check(room_id,check_in,check_out):
    #check if room exists in hotel
    query="""
        SELECT EXISTS(
            SELECT * FROM Rooms WHERE Rooms.Room_ID=?
        )
    
    """
    room_exists=sql(query,room_id)[0][0]
    if not room_exists:
        return "This room doesn't exist!"

    #check availability for the room between Check-in and Check-out 
    query="""SELECT EXISTS ( SELECT *FROM Rooms 
    
    INNER JOIN ROOM_TYPES ON Rooms.ROOM_TYPE_ID=ROOM_TYPES.ROOM_TYPE_ID
    
    WHERE Rooms.Room_ID NOT IN 
        (SELECT Rooms.Room_ID FROM Rooms  
                    INNER JOIN RESERVATIONS ON RESERVATIONS.Room_ID=Rooms.Room_ID
        WHERE
                RESERVATIONS.[Check-in] 
                BETWEEN ?  AND ?
            AND 
                RESERVATIONS.[Check-OUT]    
                BETWEEN ?  AND ?
        )
        AND Rooms.Room_ID=?
        )
    """
    room_is_available=sql(query,check_in,check_out,check_in,check_out,room_id)[0][0]
    if not room_is_available:
        return "This room isn't available!"
    return True

def load_user_details(user_email):
    query="""SELECT "First Name","Last Name",Phone,Address FROM Customers WHERE "e-mail"=?
    
    """
    user_details=dictionarify(query,sql(query,user_email))[0]
    for key,value in user_details.items():
        if value==None:
            user_details[key]=""
    return user_details

def check_diffs_and_update(old_user_details,new_users_details,user_email):
    different_keys=[]
    for key,value in old_user_details.items():
        if new_users_details[key]!=old_user_details[key]:
            different_keys.append(key)
    changes=""
    for i in different_keys:
        changes=changes+"{}='{}',".format(i,new_users_details[i])
    changes=changes[:-1]

    query='UPDATE Customers SET '+changes+' WHERE "e-mail" ="'+user_email+'"; '
    print(query)
    sql(query)

def make_reservation(room_id,check_in,check_out,user_email):
    print(room_id,check_in,check_out,user_email)
    customer_id=sql('SELECT Customer_ID FROM Customers WHERE "e-mail"=?',user_email)[0][0]
    print(customer_id)
    query='INSERT INTO RESERVATIONS (Customer_ID,Room_ID,"Check-in","Check-out") values (?, ?,?,?)'
    print(query)
    sql(query,customer_id,room_id,check_in,check_out)
