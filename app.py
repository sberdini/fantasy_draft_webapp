import os
from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit
import eventlet
eventlet.monkey_patch()  # Required for SocketIO

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# Updated players list with bye weeks (from previous)
players = [
    {"rank": 1, "name": "Ja'Marr Chase", "pos": "WR", "team": "CIN", "bye": 10},
    {"rank": 2, "name": "Bijan Robinson", "pos": "RB", "team": "ATL", "bye": 5},
    {"rank": 3, "name": "Justin Jefferson", "pos": "WR", "team": "MIN", "bye": 6},
    {"rank": 4, "name": "Saquon Barkley", "pos": "RB", "team": "PHI", "bye": 9},
    {"rank": 5, "name": "Jahmyr Gibbs", "pos": "RB", "team": "DET", "bye": 8},
    {"rank": 6, "name": "CeeDee Lamb", "pos": "WR", "team": "DAL", "bye": 10},
    {"rank": 7, "name": "Puka Nacua", "pos": "WR", "team": "LAR", "bye": 8},
    {"rank": 8, "name": "Malik Nabers", "pos": "WR", "team": "NYG", "bye": 14},
    {"rank": 9, "name": "Christian McCaffrey", "pos": "RB", "team": "SF", "bye": 14},
    {"rank": 10, "name": "Amon-Ra St. Brown", "pos": "WR", "team": "DET", "bye": 8},
    {"rank": 11, "name": "Ashton Jeanty", "pos": "RB", "team": "LV", "bye": 8},
    {"rank": 12, "name": "De'Von Achane", "pos": "RB", "team": "MIA", "bye": 12},
    {"rank": 13, "name": "Nico Collins", "pos": "WR", "team": "HOU", "bye": 6},
    {"rank": 14, "name": "Brian Thomas Jr.", "pos": "WR", "team": "JAC", "bye": 8},
    {"rank": 15, "name": "A.J. Brown", "pos": "WR", "team": "PHI", "bye": 9},
    {"rank": 16, "name": "Jonathan Taylor", "pos": "RB", "team": "IND", "bye": 11},
    {"rank": 17, "name": "Josh Jacobs", "pos": "RB", "team": "GB", "bye": 5},
    {"rank": 18, "name": "Derrick Henry", "pos": "RB", "team": "BAL", "bye": 7},
    {"rank": 19, "name": "Brock Bowers", "pos": "TE", "team": "LV", "bye": 8},
    {"rank": 20, "name": "Trey McBride", "pos": "TE", "team": "ARI", "bye": 8},
    {"rank": 21, "name": "Bucky Irving", "pos": "RB", "team": "TB", "bye": 9},
    {"rank": 22, "name": "Drake London", "pos": "WR", "team": "ATL", "bye": 5},
    {"rank": 23, "name": "Kyren Williams", "pos": "RB", "team": "LAR", "bye": 8},
    {"rank": 24, "name": "James Cook", "pos": "RB", "team": "BUF", "bye": 7},
    {"rank": 25, "name": "Josh Allen", "pos": "QB", "team": "BUF", "bye": 7},
    {"rank": 26, "name": "Lamar Jackson", "pos": "QB", "team": "BAL", "bye": 7},
    {"rank": 27, "name": "Marvin Harrison Jr.", "pos": "WR", "team": "ARI", "bye": 8},
    {"rank": 28, "name": "Devonta Smith", "pos": "WR", "team": "PHI", "bye": 9},
    {"rank": 29, "name": "Isiah Pacheco", "pos": "RB", "team": "KC", "bye": 10},
    {"rank": 30, "name": "Travis Etienne Jr.", "pos": "RB", "team": "JAC", "bye": 8},
    {"rank": 31, "name": "Sam LaPorta", "pos": "TE", "team": "DET", "bye": 8},
    {"rank": 32, "name": "Chris Olave", "pos": "WR", "team": "NO", "bye": 11},
    {"rank": 33, "name": "Davante Adams", "pos": "WR", "team": "LV", "bye": 8},
    {"rank": 34, "name": "Jalen Hurts", "pos": "QB", "team": "PHI", "bye": 9},
    {"rank": 35, "name": "Patrick Mahomes", "pos": "QB", "team": "KC", "bye": 10},
    {"rank": 36, "name": "Alvin Kamara", "pos": "RB", "team": "NO", "bye": 11},
    {"rank": 37, "name": "Rachaad White", "pos": "RB", "team": "TB", "bye": 9},
    {"rank": 38, "name": "Deebo Samuel Sr.", "pos": "WR", "team": "SF", "bye": 14},
    {"rank": 39, "name": "DK Metcalf", "pos": "WR", "team": "SEA", "bye": 8},
    {"rank": 40, "name": "Garrett Wilson", "pos": "WR", "team": "NYJ", "bye": 9},
    {"rank": 41, "name": "Travis Kelce", "pos": "TE", "team": "KC", "bye": 10},
    {"rank": 42, "name": "Joe Mixon", "pos": "RB", "team": "HOU", "bye": 6},
    {"rank": 43, "name": "Aaron Jones", "pos": "RB", "team": "MIN", "bye": 6},
    {"rank": 44, "name": "Mike Evans", "pos": "WR", "team": "TB", "bye": 9},
    {"rank": 45, "name": "DJ Moore", "pos": "WR", "team": "CHI", "bye": 5},
    {"rank": 46, "name": "C.J. Stroud", "pos": "QB", "team": "HOU", "bye": 6},
    {"rank": 47, "name": "Kyler Murray", "pos": "QB", "team": "ARI", "bye": 8},
    {"rank": 48, "name": "Kenneth Walker III", "pos": "RB", "team": "SEA", "bye": 8},
    {"rank": 49, "name": "David Montgomery", "pos": "RB", "team": "DET", "bye": 8},
    {"rank": 50, "name": "Najee Harris", "pos": "RB", "team": "PIT", "bye": 5},
    {"rank": 51, "name": "Tee Higgins", "pos": "WR", "team": "CIN", "bye": 10},
    {"rank": 52, "name": "Ladd McConkey", "pos": "WR", "team": "LAC", "bye": 12},
    {"rank": 53, "name": "Jaylen Waddle", "pos": "WR", "team": "MIA", "bye": 12},
    {"rank": 54, "name": "George Kittle", "pos": "TE", "team": "SF", "bye": 14},
    {"rank": 55, "name": "Joe Burrow", "pos": "QB", "team": "CIN", "bye": 10},
    {"rank": 56, "name": "Dak Prescott", "pos": "QB", "team": "DAL", "bye": 10},
    {"rank": 57, "name": "Breece Hall", "pos": "RB", "team": "NYJ", "bye": 9},
    {"rank": 58, "name": "Cooper Kupp", "pos": "WR", "team": "LAR", "bye": 8},
    {"rank": 59, "name": "Zay Flowers", "pos": "WR", "team": "BAL", "bye": 7},
    {"rank": 60, "name": "Rhamondre Stevenson", "pos": "RB", "team": "NE", "bye": 14},
    {"rank": 61, "name": "Brandon Aiyuk", "pos": "WR", "team": "SF", "bye": 14},
    {"rank": 62, "name": "Dalton Kincaid", "pos": "TE", "team": "BUF", "bye": 7},
    {"rank": 63, "name": "Calvin Ridley", "pos": "WR", "team": "TEN", "bye": 10},
    {"rank": 64, "name": "D'Andre Swift", "pos": "RB", "team": "CHI", "bye": 5},
    {"rank": 65, "name": "Terry McLaurin", "pos": "WR", "team": "WAS", "bye": 12},
    {"rank": 66, "name": "Mark Andrews", "pos": "TE", "team": "BAL", "bye": 7},
    {"rank": 67, "name": "Javonte Williams", "pos": "RB", "team": "DEN", "bye": 12},
    {"rank": 68, "name": "Amari Cooper", "pos": "WR", "team": "CLE", "bye": 9},
    {"rank": 69, "name": "Anthony Richardson", "pos": "QB", "team": "IND", "bye": 11},
    {"rank": 70, "name": "James Conner", "pos": "RB", "team": "ARI", "bye": 8},
    {"rank": 71, "name": "Stefon Diggs", "pos": "WR", "team": "HOU", "bye": 6},
    {"rank": 72, "name": "Evan Engram", "pos": "TE", "team": "JAC", "bye": 8},
    {"rank": 73, "name": "Zamir White", "pos": "RB", "team": "LV", "bye": 8},
    {"rank": 74, "name": "Rashee Rice", "pos": "WR", "team": "KC", "bye": 10},
    {"rank": 75, "name": "J.K. Dobbins", "pos": "RB", "team": "LAC", "bye": 12},
    {"rank": 76, "name": "Justin Fields", "pos": "QB", "team": "PIT", "bye": 5},
    {"rank": 77, "name": "George Pickens", "pos": "WR", "team": "PIT", "bye": 5},
    {"rank": 78, "name": "David Njoku", "pos": "TE", "team": "CLE", "bye": 9},
    {"rank": 79, "name": "Christian Watson", "pos": "WR", "team": "GB", "bye": 5},
    {"rank": 80, "name": "Jayden Daniels", "pos": "QB", "team": "WAS", "bye": 12},
    {"rank": 81, "name": "Tony Pollard", "pos": "RB", "team": "TEN", "bye": 10},
    {"rank": 82, "name": "Chris Godwin", "pos": "WR", "team": "TB", "bye": 9},
    {"rank": 83, "name": "Raheem Mostert", "pos": "RB", "team": "MIA", "bye": 12},
    {"rank": 84, "name": "Jake Ferguson", "pos": "TE", "team": "DAL", "bye": 10},
    {"rank": 85, "name": "Tank Dell", "pos": "WR", "team": "HOU", "bye": 6},
    {"rank": 86, "name": "Nick Chubb", "pos": "RB", "team": "CLE", "bye": 9},
    {"rank": 87, "name": "Jordan Addison", "pos": "WR", "team": "MIN", "bye": 6},
    {"rank": 88, "name": "Cole Kmet", "pos": "TE", "team": "CHI", "bye": 5},
    {"rank": 89, "name": "Devin Singletary", "pos": "RB", "team": "NYG", "bye": 14},
    {"rank": 90, "name": "Courtland Sutton", "pos": "WR", "team": "DEN", "bye": 12},
    {"rank": 91, "name": "Jared Goff", "pos": "QB", "team": "DET", "bye": 8},
    {"rank": 92, "name": "Diontae Johnson", "pos": "WR", "team": "CAR", "bye": 14},
    {"rank": 93, "name": "Austin Ekeler", "pos": "RB", "team": "WAS", "bye": 12},
    {"rank": 94, "name": "Rome Odunze", "pos": "WR", "team": "CHI", "bye": 5},
    {"rank": 95, "name": "Pat Freiermuth", "pos": "TE", "team": "PIT", "bye": 5},
    {"rank": 96, "name": "Gus Edwards", "pos": "RB", "team": "LAC", "bye": 12},
    {"rank": 97, "name": "Hollywood Brown", "pos": "WR", "team": "KC", "bye": 10},
    {"rank": 98, "name": "Aaron Rodgers", "pos": "QB", "team": "NYJ", "bye": 9},
    {"rank": 99, "name": "Chuba Hubbard", "pos": "RB", "team": "CAR", "bye": 14},
    {"rank": 100, "name": "Jauan Jennings", "pos": "WR", "team": "SF", "bye": 14},
    {"rank": 101, "name": "Caleb Williams", "pos": "QB", "team": "CHI", "bye": 5},
    {"rank": 102, "name": "Zach Charbonnet", "pos": "RB", "team": "SEA", "bye": 8},
    {"rank": 103, "name": "Xavier Worthy", "pos": "WR", "team": "KC", "bye": 10},
    {"rank": 104, "name": "Dallas Goedert", "pos": "TE", "team": "PHI", "bye": 9},
    {"rank": 105, "name": "Jerome Ford", "pos": "RB", "team": "CLE", "bye": 9},
    {"rank": 106, "name": "Christian Kirk", "pos": "WR", "team": "JAC", "bye": 8},
    {"rank": 107, "name": "Brian Robinson Jr.", "pos": "RB", "team": "WAS", "bye": 12},
    {"rank": 108, "name": "Hunter Henry", "pos": "TE", "team": "NE", "bye": 14},
    {"rank": 109, "name": "Jaxon Smith-Njigba", "pos": "WR", "team": "SEA", "bye": 8},
    {"rank": 110, "name": "Ezekiel Elliott", "pos": "RB", "team": "DAL", "bye": 10},
    {"rank": 111, "name": "Curtis Samuel", "pos": "WR", "team": "BUF", "bye": 7},
    {"rank": 112, "name": "Tua Tagovailoa", "pos": "QB", "team": "MIA", "bye": 12},
    {"rank": 113, "name": "Tyjae Spears", "pos": "RB", "team": "TEN", "bye": 10},
    {"rank": 114, "name": "Jakobi Meyers", "pos": "WR", "team": "LV", "bye": 8},
    {"rank": 115, "name": "Dalton Schultz", "pos": "TE", "team": "HOU", "bye": 6},
    {"rank": 116, "name": "Jonah Williams", "pos": "RB", "team": "FA", "bye": 0},
    {"rank": 117, "name": "Demario Douglas", "pos": "WR", "team": "NE", "bye": 14},
    {"rank": 118, "name": "Matthew Stafford", "pos": "QB", "team": "LAR", "bye": 8},
    {"rank": 119, "name": "Chase Brown", "pos": "RB", "team": "CIN", "bye": 10},
    {"rank": 120, "name": "Khalil Shakir", "pos": "WR", "team": "BUF", "bye": 7},
    {"rank": 121, "name": "T.J. Hockenson", "pos": "TE", "team": "MIN", "bye": 6},
    {"rank": 122, "name": "Deandre Hopkins", "pos": "WR", "team": "TEN", "bye": 10},
    {"rank": 123, "name": "Blake Corum", "pos": "RB", "team": "LAR", "bye": 8},
    {"rank": 124, "name": "Tyler Lockett", "pos": "WR", "team": "SEA", "bye": 8},
    {"rank": 125, "name": "Brock Purdy", "pos": "QB", "team": "SF", "bye": 14},
    {"rank": 126, "name": "Kendre Miller", "pos": "RB", "team": "NO", "bye": 11},
    {"rank": 127, "name": "Josh Downs", "pos": "WR", "team": "IND", "bye": 11},
    {"rank": 128, "name": "Isaiah Likely", "pos": "TE", "team": "BAL", "bye": 7},
    {"rank": 129, "name": "Alexander Mattison", "pos": "RB", "team": "LV", "bye": 8},
    {"rank": 130, "name": "Jerry Jeudy", "pos": "WR", "team": "CLE", "bye": 9},
    {"rank": 131, "name": "Rico Dowdle", "pos": "RB", "team": "DAL", "bye": 10},
    {"rank": 132, "name": "Gabe Davis", "pos": "WR", "team": "JAC", "bye": 8},
    {"rank": 133, "name": "Taysom Hill", "pos": "TE", "team": "NO", "bye": 11},
    {"rank": 134, "name": "Justin Herbert", "pos": "QB", "team": "LAC", "bye": 12},
    {"rank": 135, "name": "Roschon Johnson", "pos": "RB", "team": "CHI", "bye": 5},
    {"rank": 136, "name": "Rashid Shaheed", "pos": "WR", "team": "NO", "bye": 11},
    {"rank": 137, "name": "Trey Benson", "pos": "RB", "team": "ARI", "bye": 8},
    {"rank": 138, "name": "J.J. McCarthy", "pos": "QB", "team": "MIN", "bye": 6},
    {"rank": 139, "name": "Demarcus Robinson", "pos": "WR", "team": "LAR", "bye": 8},
    {"rank": 140, "name": "Ty Chandler", "pos": "RB", "team": "MIN", "bye": 6},
    {"rank": 141, "name": "Khalil Herbert", "pos": "RB", "team": "CHI", "bye": 5},
    {"rank": 142, "name": "Brandin Cooks", "pos": "WR", "team": "DAL", "bye": 10},
    {"rank": 143, "name": "Jaleel McLaughlin", "pos": "RB", "team": "DEN", "bye": 12},
    {"rank": 144, "name": "Romeo Doubs", "pos": "WR", "team": "GB", "bye": 5},
    {"rank": 145, "name": "Chigoziem Okonkwo", "pos": "TE", "team": "TEN", "bye": 10},
    {"rank": 146, "name": "Jordan Love", "pos": "QB", "team": "GB", "bye": 5},
    {"rank": 147, "name": "Dameon Pierce", "pos": "RB", "team": "HOU", "bye": 6},
    {"rank": 148, "name": "Dontayvion Wicks", "pos": "WR", "team": "GB", "bye": 5},
    {"rank": 149, "name": "Keenan Allen", "pos": "WR", "team": "CHI", "bye": 5},
    {"rank": 150, "name": "Juwan Johnson", "pos": "TE", "team": "NO", "bye": 11},
    {"rank": 151, "name": "Jaylen Warren", "pos": "RB", "team": "PIT", "bye": 5},
    {"rank": 152, "name": "Michael Pittman Jr.", "pos": "WR", "team": "IND", "bye": 11},
    {"rank": 153, "name": "Bo Nix", "pos": "QB", "team": "DEN", "bye": 12},
    {"rank": 154, "name": "Marquise Brown", "pos": "WR", "team": "KC", "bye": 10},
    {"rank": 155, "name": "Antonio Gibson", "pos": "RB", "team": "NE", "bye": 14},
    {"rank": 156, "name": "Luke Musgrave", "pos": "TE", "team": "GB", "bye": 5},
    {"rank": 157, "name": "Keaton Mitchell", "pos": "RB", "team": "BAL", "bye": 7},
    {"rank": 158, "name": "Tucker Kraft", "pos": "TE", "team": "GB", "bye": 5},
    {"rank": 159, "name": "Quentin Johnston", "pos": "WR", "team": "LAC", "bye": 12},
    {"rank": 160, "name": "Ray Davis", "pos": "RB", "team": "BUF", "bye": 7},
    {"rank": 161, "name": "Adonai Mitchell", "pos": "WR", "team": "IND", "bye": 11},
    {"rank": 162, "name": "Baker Mayfield", "pos": "QB", "team": "TB", "bye": 9},
    {"rank": 163, "name": "Jonnu Smith", "pos": "TE", "team": "MIA", "bye": 12},
    {"rank": 164, "name": "Kimani Vidal", "pos": "RB", "team": "LAC", "bye": 12},
    {"rank": 165, "name": "Michael Wilson", "pos": "WR", "team": "ARI", "bye": 8},
    {"rank": 166, "name": "Jahan Dotson", "pos": "WR", "team": "WAS", "bye": 12},
    {"rank": 167, "name": "Tyler Allgeier", "pos": "RB", "team": "ATL", "bye": 5},
    {"rank": 168, "name": "Will Levis", "pos": "QB", "team": "TEN", "bye": 10},
    {"rank": 169, "name": "Wan'Dale Robinson", "pos": "WR", "team": "NYG", "bye": 14},
    {"rank": 170, "name": "Elijah Moore", "pos": "WR", "team": "CLE", "bye": 9},
    {"rank": 171, "name": "Audric Estime", "pos": "RB", "team": "DEN", "bye": 12},
    {"rank": 172, "name": "Cade Otton", "pos": "TE", "team": "TB", "bye": 9},
    {"rank": 173, "name": "Sam Darnold", "pos": "QB", "team": "MIN", "bye": 6},
    {"rank": 174, "name": "MarShawn Lloyd", "pos": "RB", "team": "GB", "bye": 5},
    {"rank": 175, "name": "Darius Slayton", "pos": "WR", "team": "NYG", "bye": 14},
    {"rank": 176, "name": "Tyreek Hill", "pos": "WR", "team": "MIA", "bye": 12},
    {"rank": 177, "name": "Justice Hill", "pos": "RB", "team": "BAL", "bye": 7},
    {"rank": 178, "name": "Mike Gesicki", "pos": "TE", "team": "CIN", "bye": 10},
    {"rank": 179, "name": "Drake Maye", "pos": "QB", "team": "NE", "bye": 14},
    {"rank": 180, "name": "Joshua Palmer", "pos": "WR", "team": "LAC", "bye": 12},
    {"rank": 181, "name": "D'Onta Foreman", "pos": "RB", "team": "CLE", "bye": 9},
    {"rank": 182, "name": "Troy Franklin", "pos": "WR", "team": "DEN", "bye": 12},
    {"rank": 183, "name": "Emari Demercado", "pos": "RB", "team": "ARI", "bye": 8},
    {"rank": 184, "name": "Colston Loveland", "pos": "TE", "team": "CHI", "bye": 5},
    {"rank": 185, "name": "Geno Smith", "pos": "QB", "team": "SEA", "bye": 8},
    {"rank": 186, "name": "K.J. Osborn", "pos": "WR", "team": "NE", "bye": 14},
    {"rank": 187, "name": "Tank Bigsby", "pos": "RB", "team": "JAC", "bye": 8},
    {"rank": 188, "name": "Tyler Conklin", "pos": "TE", "team": "NYJ", "bye": 9},
    {"rank": 189, "name": "Malik Washington", "pos": "WR", "team": "MIA", "bye": 12},
    {"rank": 190, "name": "Miles Sanders", "pos": "RB", "team": "CAR", "bye": 14},
    {"rank": 191, "name": "Daniel Jones", "pos": "QB", "team": "NYG", "bye": 14},
    {"rank": 192, "name": "Andrei Iosivas", "pos": "WR", "team": "CIN", "bye": 10},
    {"rank": 193, "name": "Zach Ertz", "pos": "TE", "team": "WAS", "bye": 12},
    {"rank": 194, "name": "A.J. Dillon", "pos": "RB", "team": "GB", "bye": 5},
    {"rank": 195, "name": "Rondale Moore", "pos": "WR", "team": "ATL", "bye": 5},
    {"rank": 196, "name": "Desmond Ridder", "pos": "QB", "team": "ATL", "bye": 5},
    {"rank": 197, "name": "Jonathan Mingo", "pos": "WR", "team": "CAR", "bye": 14},
    {"rank": 198, "name": "Kenneth Gainwell", "pos": "RB", "team": "PHI", "bye": 9},
    {"rank": 199, "name": "Donovan Peoples-Jones", "pos": "WR", "team": "DET", "bye": 8},
    {"rank": 200, "name": "Hayden Hurst", "pos": "TE", "team": "LAC", "bye": 12},
    {"rank": 201, "name": "Brandon Aubrey", "pos": "K", "team": "DAL", "bye": 10},
    {"rank": 202, "name": "Cameron Dicker", "pos": "K", "team": "LAC", "bye": 12},
    {"rank": 203, "name": "Matt Gay", "pos": "K", "team": "WAS", "bye": 12},
    {"rank": 204, "name": "Tyler Bass", "pos": "K", "team": "BUF", "bye": 7},
    {"rank": 205, "name": "Jake Elliott", "pos": "K", "team": "PHI", "bye": 9},
    {"rank": 206, "name": "Justin Tucker", "pos": "K", "team": "BAL", "bye": 7},
    {"rank": 207, "name": "Harrison Butker", "pos": "K", "team": "KC", "bye": 10},
    {"rank": 208, "name": "Chase McLaughlin", "pos": "K", "team": "TB", "bye": 9},
    {"rank": 209, "name": "Jake Bates", "pos": "K", "team": "DET", "bye": 8},
    {"rank": 210, "name": "Evan McPherson", "pos": "K", "team": "CIN", "bye": 10},
    {"rank": 211, "name": "Ka'imi Fairbairn", "pos": "K", "team": "HOU", "bye": 6},
    {"rank": 212, "name": "Chris Boswell", "pos": "K", "team": "PIT", "bye": 5},
    {"rank": 213, "name": "Dustin Hopkins", "pos": "K", "team": "CLE", "bye": 9},
    {"rank": 214, "name": "Daniel Carlson", "pos": "K", "team": "LV", "bye": 8},
    {"rank": 215, "name": "Younghoe Koo", "pos": "K", "team": "ATL", "bye": 5},
    {"rank": 216, "name": "Jason Myers", "pos": "K", "team": "SEA", "bye": 8},
    {"rank": 217, "name": "Jason Sanders", "pos": "K", "team": "MIA", "bye": 12},
    {"rank": 218, "name": "Blake Grupe", "pos": "K", "team": "NO", "bye": 11},
    {"rank": 219, "name": "Matt Prater", "pos": "K", "team": "ARI", "bye": 8},
    {"rank": 220, "name": "Cairo Santos", "pos": "K", "team": "CHI", "bye": 5},
    {"rank": 221, "name": "Wil Lutz", "pos": "K", "team": "DEN", "bye": 12},
    {"rank": 222, "name": "Eddy Pineiro", "pos": "K", "team": "CAR", "bye": 14},
    {"rank": 223, "name": "Joey Slye", "pos": "K", "team": "NE", "bye": 14},
    {"rank": 224, "name": "Graham Gano", "pos": "K", "team": "NYG", "bye": 14},
    {"rank": 225, "name": "Anders Carlson", "pos": "K", "team": "SF", "bye": 14},
    {"rank": 226, "name": "Chad Ryland", "pos": "K", "team": "GB", "bye": 5},
    {"rank": 227, "name": "Joshua Karty", "pos": "K", "team": "LAR", "bye": 8},
    {"rank": 228, "name": "Randy Bullock", "pos": "K", "team": "JAC", "bye": 8},
    {"rank": 229, "name": "Riley Patterson", "pos": "K", "team": "NYJ", "bye": 9},
    {"rank": 230, "name": "Greg Joseph", "pos": "K", "team": "IND", "bye": 11},
    {"rank": 231, "name": "Brett Maher", "pos": "K", "team": "MIN", "bye": 6},
    {"rank": 232, "name": "Nick Folk", "pos": "K", "team": "TEN", "bye": 10},
    {"rank": 233, "name": "Denver Broncos", "pos": "DST", "team": "DEN", "bye": 12},
    {"rank": 234, "name": "Philadelphia Eagles", "pos": "DST", "team": "PHI", "bye": 9},
    {"rank": 235, "name": "Baltimore Ravens", "pos": "DST", "team": "BAL", "bye": 7},
    {"rank": 236, "name": "Pittsburgh Steelers", "pos": "DST", "team": "PIT", "bye": 5},
    {"rank": 237, "name": "Minnesota Vikings", "pos": "DST", "team": "MIN", "bye": 6},
    {"rank": 238, "name": "Houston Texans", "pos": "DST", "team": "HOU", "bye": 6},
    {"rank": 239, "name": "New York Jets", "pos": "DST", "team": "NYJ", "bye": 9},
    {"rank": 240, "name": "Cleveland Browns", "pos": "DST", "team": "CLE", "bye": 9},
    {"rank": 241, "name": "San Francisco 49ers", "pos": "DST", "team": "SF", "bye": 14},
    {"rank": 242, "name": "Dallas Cowboys", "pos": "DST", "team": "DAL", "bye": 10},
    {"rank": 243, "name": "Kansas City Chiefs", "pos": "DST", "team": "KC", "bye": 10},
    {"rank": 244, "name": "Buffalo Bills", "pos": "DST", "team": "BUF", "bye": 7},
    {"rank": 245, "name": "Miami Dolphins", "pos": "DST", "team": "MIA", "bye": 12},
    {"rank": 246, "name": "Chicago Bears", "pos": "DST", "team": "CHI", "bye": 5},
    {"rank": 247, "name": "Indianapolis Colts", "pos": "DST", "team": "IND", "bye": 11},
    {"rank": 248, "name": "Detroit Lions", "pos": "DST", "team": "DET", "bye": 8},
    {"rank": 249, "name": "Cincinnati Bengals", "pos": "DST", "team": "CIN", "bye": 10},
    {"rank": 250, "name": "Green Bay Packers", "pos": "DST", "team": "GB", "bye": 5},
    {"rank": 251, "name": "Atlanta Falcons", "pos": "DST", "team": "ATL", "bye": 5},
    {"rank": 252, "name": "New England Patriots", "pos": "DST", "team": "NE", "bye": 14},
    {"rank": 253, "name": "Los Angeles Rams", "pos": "DST", "team": "LAR", "bye": 8},
    {"rank": 254, "name": "Tampa Bay Buccaneers", "pos": "DST", "team": "TB", "bye": 9},
    {"rank": 255, "name": "Seattle Seahawks", "pos": "DST", "team": "SEA", "bye": 8},
    {"rank": 256, "name": "Washington Commanders", "pos": "DST", "team": "WAS", "bye": 12},
    {"rank": 257, "name": "New Orleans Saints", "pos": "DST", "team": "NO", "bye": 11},
    {"rank": 258, "name": "Arizona Cardinals", "pos": "DST", "team": "ARI", "bye": 8},
    {"rank": 259, "name": "Jacksonville Jaguars", "pos": "DST", "team": "JAC", "bye": 8},
    {"rank": 260, "name": "Las Vegas Raiders", "pos": "DST", "team": "LV", "bye": 8},
    {"rank": 261, "name": "Tennessee Titans", "pos": "DST", "team": "TEN", "bye": 10},
    {"rank": 262, "name": "Carolina Panthers", "pos": "DST", "team": "CAR", "bye": 14},
    {"rank": 263, "name": "New York Giants", "pos": "DST", "team": "NYG", "bye": 14},
    {"rank": 264, "name": "Los Angeles Chargers", "pos": "DST", "team": "LAC", "bye": 12},
]

# Draft state
draft_state = {
    "teams": [],
    "rosters": {},
    "available_players": players.copy(),
    "current_round": 1,
    "current_pick": 0,
    "num_rounds": 15,
    "started": False,
    "paused": False,
    "turn_start_time": None,
    "draft_history": [],
}

def get_current_order():
    if draft_state["current_round"] % 2 == 1:
        return draft_state["teams"]
    else:
        return draft_state["teams"][::-1]

def advance_to_next_open_pick():
    num_teams = len(draft_state["teams"])
    while draft_state["current_round"] <= draft_state["num_rounds"]:
        order = get_current_order()
        team = order[draft_state["current_pick"]]
        if any(p["round"] == draft_state["current_round"] and p["team"] == team for p in draft_state["draft_history"]):
            draft_state["current_pick"] += 1
            if draft_state["current_pick"] >= num_teams:
                draft_state["current_round"] += 1
                draft_state["current_pick"] = 0
        else:
            return
    draft_state["started"] = False
    draft_state["turn_start_time"] = None
    draft_state["current_round"] = draft_state["num_rounds"] + 1
    draft_state["current_pick"] = 0

def reverse_to_previous_open_pick():
    num_teams = len(draft_state["teams"])
    while draft_state["current_round"] >= 1:
        order = get_current_order()
        team = order[draft_state["current_pick"]]
        if any(p["round"] == draft_state["current_round"] and p["team"] == team for p in draft_state["draft_history"]):
            draft_state["current_pick"] -= 1
            if draft_state["current_pick"] < 0:
                draft_state["current_round"] -= 1
                draft_state["current_pick"] = num_teams - 1
        else:
            return
    draft_state["current_round"] = 1
    draft_state["current_pick"] = 0

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    print('Join event:', data)  # Debug log
    if data.get('is_spectator'):
        session['is_spectator'] = True
        emit('update_draft', draft_state)
        return
    team_name = data.get('team', '')
    if data.get('is_admin'):
        session['is_admin'] = True
        if team_name:
            if team_name not in draft_state["teams"]:
                draft_state["teams"].append(team_name)
                draft_state["rosters"][team_name] = []
            session['team'] = team_name
        else:
            session['team'] = 'Admin'
        emit('update_draft', draft_state, broadcast=True)
    else:
        if draft_state["started"]:
            emit('join_error', {'msg': 'Draft has started, no new teams can join'})
            return
        if not team_name:
            emit('join_error', {'msg': 'Team name required'})
            return
        if team_name not in draft_state["teams"]:
            draft_state["teams"].append(team_name)
            draft_state["rosters"][team_name] = []
        session['team'] = team_name
        emit('update_draft', draft_state, broadcast=True)

@socketio.on('reorder_teams')
def handle_reorder_teams(data):
    new_order = data['new_order']
    if 'is_admin' in session and session['is_admin'] and not draft_state["started"]:
        if sorted(new_order) == sorted(draft_state["teams"]):
            draft_state["teams"] = new_order
            emit('update_draft', draft_state, broadcast=True)

@socketio.on('assign_pick')
def handle_assign_pick(data):
    if 'is_admin' in session and session['is_admin'] and not draft_state["started"]:
        team = data['team']
        player_name = data['player']
        round_num = data['round']
        player = next((p for p in draft_state["available_players"] if p['name'] == player_name), None)
        if player and team in draft_state["rosters"] and 1 <= round_num <= draft_state["num_rounds"]:
            pick_in_round = draft_state["teams"].index(team) + 1 if round_num % 2 == 1 else len(draft_state["teams"]) - draft_state["teams"].index(team)
            overall_pick = (round_num - 1) * len(draft_state["teams"]) + pick_in_round
            if not any(p["round"] == round_num and p["team"] == team for p in draft_state["draft_history"]):
                draft_state["available_players"].remove(player)
                draft_state["rosters"][team].append(player)
                draft_state["draft_history"].append({
                    "round": round_num,
                    "overall_pick": overall_pick,
                    "team": team,
                    "player": player
                })
                draft_state["draft_history"].sort(key=lambda x: x["overall_pick"])
                emit('update_draft', draft_state, broadcast=True)
            else:
                emit('error', {'msg': 'Spot already filled'})
        else:
            emit('error', {'msg': 'Invalid assignment'})

@socketio.on('start_draft')
def handle_start():
    if 'is_admin' in session and session['is_admin'] and not draft_state["started"] and len(draft_state["teams"]) >= 2:
        draft_state["started"] = True
        advance_to_next_open_pick()
        draft_state["turn_start_time"] = time.time()
        emit('update_draft', draft_state, broadcast=True)

@socketio.on('pause_draft')
def handle_pause():
    if 'is_admin' in session and session['is_admin']:
        draft_state["paused"] = not draft_state["paused"]
        emit('update_draft', draft_state, broadcast=True)

@socketio.on('revert_pick')
def handle_revert():
    if 'is_admin' in session and session['is_admin'] and draft_state["draft_history"]:
        last_pick = draft_state["draft_history"].pop()
        player = last_pick["player"]
        team = last_pick["team"]
        draft_state["rosters"][team].pop()
        draft_state["available_players"].append(player)
        reverse_to_previous_open_pick()
        draft_state["turn_start_time"] = time.time()
        emit('update_draft', draft_state, broadcast=True)

@socketio.on('admin_make_pick')
def handle_admin_pick(data):
    if 'is_admin' in session and session['is_admin'] and draft_state["started"] and not draft_state["paused"]:
        current_order = get_current_order()
        current_team = current_order[draft_state["current_pick"]]
        if data['for_team']:
            current_team = data['for_team']
        player_name = data['player']
        player = next((p for p in draft_state["available_players"] if p['name'] == player_name), None)
        if player:
            draft_state["available_players"].remove(player)
            draft_state["rosters"][current_team].append(player)
            overall_pick = ((draft_state["current_round"] - 1) * len(draft_state["teams"])) + draft_state["current_pick"] + 1
            draft_state["draft_history"].append({
                "round": draft_state["current_round"],
                "overall_pick": overall_pick,
                "team": current_team,
                "player": player
            })
            advance_to_next_open_pick()
            if draft_state["current_round"] > draft_state["num_rounds"]:
                draft_state["started"] = False
                draft_state["turn_start_time"] = None
            else:
                draft_state["turn_start_time"] = time.time()
            emit('update_draft', draft_state, broadcast=True)

@socketio.on('make_pick')
def handle_pick(data):
    if not draft_state["started"] or draft_state["paused"] or 'team' not in session:
        return
    current_order = get_current_order()
    current_team = current_order[draft_state["current_pick"]]
    if session['team'] != current_team:
        return
    player_name = data['player']
    player = next((p for p in draft_state["available_players"] if p['name'] == player_name), None)
    if player:
        draft_state["available_players"].remove(player)
        draft_state["rosters"][current_team].append(player)
        overall_pick = ((draft_state["current_round"] - 1) * len(draft_state["teams"])) + draft_state["current_pick"] + 1
        draft_state["draft_history"].append({
            "round": draft_state["current_round"],
            "overall_pick": overall_pick,
            "team": current_team,
            "player": player
        })
        advance_to_next_open_pick()
        if draft_state["current_round"] > draft_state["num_rounds"]:
            draft_state["started"] = False
            draft_state["turn_start_time"] = None
        else:
            draft_state["turn_start_time"] = time.time()
        emit('update_draft', draft_state, broadcast=True)

@socketio.on('connect')
def handle_connect():
    emit('update_draft', draft_state)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)