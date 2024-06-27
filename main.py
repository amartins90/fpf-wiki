from pdfquery import PDFQuery
import re
import os
from datetime import date

def readFile(file):
    filename = file.split('-')
    id = filename[1][:-4]
    if filename[0] == 'finance':
        match_date, match_time, home_team, away_team, attendance = getFinanceData(file)
        saveData(id, match_date=match_date, match_time=match_time, home_team=home_team, away_team=away_team, attendance=attendance)
    elif filename[0] == 'scoresheet':
        match_result, venue = getScoresheetData(file)
        saveData(id, match_result=match_result, venue=venue)

def getFinanceData(file):
    print("Get finance data from " + file)
    pdf = PDFQuery(assets_path + "/" + file)
    pdf.load()

    # get match and date
    match_date_time = pdf.pq('LTTextBoxHorizontal:contains("Data: ")').text()

    # get attendance
    tmpFile = 'tmp/tmp.xml'
    pdf.tree.write(tmpFile, pretty_print = True)
    totals = pdf.pq('LTTextBoxHorizontal:contains("TOTAIS ")')[0].layout
    totals_p1 = round(totals.bbox[1], 3)
    totals_p2 = round(totals.bbox[3], 3)
    with open(tmpFile, 'r') as file:
        data = file.read()
        attendance_pattern = "bbox=\"\[\d{1,3}.\d{1,3}, " + str(totals_p1) + ", \d{1,3}.\d{1,3}, " + str(totals_p2) + "\]\" index=\"\d+\">(\d+) <\/LTTextBoxHorizontal>"
        attendance = re.findall(attendance_pattern, data)
        if attendance:
            attendance = attendance[-1]
        
    match_date, match_time, home_team, away_team = transformMatchDataTime(match_date_time)
    return match_date, match_time, home_team, away_team, attendance

def getScoresheetData(file):
    print("Get scoresheet data from " + file)
    pdf = PDFQuery(assets_path + "/" + file)
    scoresheet_data = pdf.extract([
        ('with_formatter', 'text'),
        ('final_result', 'LTTextLineHorizontal:contains("Resultado Final: ")'),
        ('venue', 'LTTextLineHorizontal:contains("Estádio ")')
    ])
    match_result, venue = transformScoresheetData(scoresheet_data)
    return match_result, venue

def transformMatchDataTime(match_date_time):
    date_pattern = "\d{2}/\d{2}/\d{4}"
    match_date = re.findall(date_pattern, match_date_time)

    time_pattern = "\d{2}:\d{2}"
    match_time = re.findall(time_pattern, match_date_time)

    position = match_date_time.find("Jogo: ")
    teams = re.sub("Jogo: ", '', match_date_time[position:])
    teams_list = [team.strip() for team in teams.split('x')]

    return match_date[0], match_time[0], teams_list[0], teams_list[1]

def transformScoresheetData(scoresheet_data):
    result_pattern = "\d+ X \d+"
    match_result = re.findall(result_pattern, scoresheet_data['final_result'])
    if match_result:
        match_result = match_result[0]
    else:
        match_result = '-'

    venue = scoresheet_data['venue'].split('/')[0].strip()

    return match_result, venue

def saveData(id, **kwargs):
    if id not in data.keys():
        data[id] = {}

    for item in kwargs:
        data[id][item] = kwargs[item]
        if item == 'attendance':
            attendance_list[id] = int(kwargs[item])

def sortAttendance(all, reverse=False):
    return dict(sorted(all.items(), key=lambda x: x[1], reverse=reverse))

def filterData(all):
    filteredData = {}
    for key, value in all.items():
        if len(filteredData) < 10:
            filteredData[key] = {
                'no': len(filteredData) + 1,
                'attendance': value,
                'home': data[key]['home_team'],
                'score': data[key]['match_result'],
                'away': data[key]['away_team'],
                'venue': data[key]['venue'],
                'date': data[key]['match_date'] + ' ' + data[key]['match_time'],
                'reference': reference.format(year, competition_id, key, key)
            } 
    return filteredData

def generateOutput(attendance_list_desc, attendance_list_asc):
    with open('output.txt', 'w') as file:
        file.write('=== Público ===\n')
        file.write('; Maiores públicos\n')
        file.write('Estes são os dez maiores públicos do campeonato:\n')
        file.write('{| class="wikitable"\n')
        file.write('|-\n')
        file.write('!width="30" |N.º\n')
        file.write('!width="70" |Público{{nota de rodapé|nome=PP|Considera-se apenas o público pagante.}}\n')
        file.write('!width="170"|Mandante\n')
        file.write('!width="50" |Placar\n')
        file.write('!width="170"|Visitante\n')
        file.write('!width="130"|Estádio\n')
        file.write('!width="110"|Data\n')
        file.write('!width="30" |{{Tooltip|Ref.|Referências}}\n')
        for key, match in attendance_list_desc.items():
            file.write('|-\n')
            file.write('!' + str(match['no']) + '\n')
            file.write('|align="right"|{{{{formatnum:{}}}}}\n'.format(str(match['attendance'])))
            file.write('|align="right"|{}\n'.format(getTeamWikipediaStyle(match['home'])))
            file.write('|align="center"|{}\n'.format(getScoreWikipediaStyle(match['score'])))
            file.write('|align="left"|{}\n'.format(getTeamWikipediaStyle(match['away'])))
            file.write('|' + match['venue'] + '\n')
            file.write('|' + match['date'] + '\n')
            file.write('|align=center|<ref>{{{{citar web|URL={}|título={}|data={}|publicado=FPF|acessodata={}}}}}</ref>\n'.format(match['reference'], getTitle(match), transformDate(match['date']), transformDate(date.today().strftime('%d/%m/%Y'))))
        file.write('|}\n')
        file.write('; Menores públicos\n')
        file.write('Estes são os dez menores públicos do campeonato:\n')
        file.write('\n')
        file.write('{| class="wikitable"\n')
        file.write('|-\n')
        file.write('!width="30" |N.º\n')
        file.write('!width="70" |Público{{nota de rodapé|nome=PP|Considera-se apenas o público pagante.}}\n')
        file.write('!width="170"|Mandante\n')
        file.write('!width="50" |Placar\n')
        file.write('!width="170"|Visitante\n')
        file.write('!width="130"|Estádio\n')
        file.write('!width="110"|Data\n')
        file.write('!width="30" |{{Tooltip|Ref.|Referências}}\n')
        for key, match in attendance_list_asc.items():
            file.write('|-\n')
            file.write('!' + str(match['no']) + '\n')
            file.write('|align="right"|{{{{formatnum:{}}}}}\n'.format(str(match['attendance'])))
            file.write('|align="right"|{}\n'.format(getTeamWikipediaStyle(match['home'])))
            file.write('|align="center"|{}\n'.format(getScoreWikipediaStyle(match['score'])))
            file.write('|align="left"|{}\n'.format(getTeamWikipediaStyle(match['away'])))
            file.write('|' + match['venue'] + '\n')
            file.write('|' + match['date'] + '\n')
            file.write('|align=center|<ref>{{{{citar web|URL={}|título={}|data={}|publicado=FPF|acessodata={}}}}}</ref>\n'.format(match['reference'], getTitle(match), transformDate(match['date']), transformDate(date.today().strftime('%d/%m/%Y'))))
        file.write('|}\n')

def getTeamWikipediaStyle(team):
    if team == 'AEA - Araçatuba':
        return '{{Futebol Araçatuba|cidade=antes}}'
    if team == 'Atlético Mogi':
        return '{{Futebol Atlético Mogi|cidade=antes}}'
    if team == 'Barcelona Esportivo':
        return '{{Futebol Barcelona-SP|cidade=antes}}'
    if team == 'Colorado Caieiras':
        return '{{Futebol Colorado Caieiras|cidade=antes}}'
    if team == 'ECUS':
        return '{{Futebol ECUS|cidade=antes}}'
    if team == 'Fernandópolis':
        return '{{Futebol Fernandópolis|cidade=antes}}'
    if team == 'AA Flamengo':
        return '{{Futebol Flamengo-SP|cidade=antes}}'
    if team == 'Inter Bebedouro':
        return '{{Futebol Inter de Bebedouro|cidade=antes}}'
    if team == 'Manthiqueira':
        return '{{Futebol Manthiqueira|cidade=antes}}'
    if team == 'Mauá Futebol':
        return '{{Futebol Mauá|cidade=antes}}'
    if team == 'Mauaense':
        return '{{Futebol Mauaense|cidade=antes}}'
    if team == 'Olímpia':
        return '{{Futebol Olímpia-SP|cidade=antes}}'
    if team == 'Paulista':
        return '{{Futebol Paulista|cidade=antes}}'
    if team == 'São Carlos FL':
        return '{{Futebol São Carlos|cidade=antes}}'
    if team == 'Tanabi':
        return '{{Futebol Tanabi|cidade=antes}}'
    if team == 'Tupã':
        return '{{Futebol Tupã|cidade=antes}}'
    if team == 'União Mogi':
        return '{{Futebol União Mogi|cidade=antes}}'
    return None

def getScoreWikipediaStyle(score):
    return score.replace('X', '-').replace(' ', '')

def getTitle(match):
    return 'Boletim Financeiro: ' + match['home'] + ' ' + getScoreWikipediaStyle(match['score']) + ' ' + match['away']

def transformDate(datetime):
    date = re.findall('\d{2}/\d{2}/\d{4}', datetime)
    if date[0]:
        day_month_year = date[0].split('/')
        day = int(day_month_year[0])
        month = int(day_month_year[1])
        if month == 1:
            month_name = 'janeiro'
        if month == 2:
            month_name = 'fevereiro'
        if month == 3:
            month_name = 'março'
        if month == 4:
            month_name = 'abril'
        if month == 5:
            month_name = 'maio'
        if month == 6:
            month_name = 'junho'
        if month == 7:
            month_name = 'julho'
        if month == 8:
            month_name = 'agosto'
        if month == 9:
            month_name = 'setembro'
        if month == 10:
            month_name = 'outubro'
        if month == 11:
            month_name = 'novembro'
        if month == 12:
            month_name = 'dezembro'
        year = day_month_year[2]
        return str(day) + ' de ' + month_name + ' de ' + year
    return None

if __name__ == "__main__":
    assets_path = os.getcwd() + '/assets'
    files = os.listdir(assets_path)

    year = 2024
    competition_id = 74104
    reference = "https://conteudo.fpf.org.br/Competicoes/{}/{}/boletins-financeiros/{}/boletins/{}.pdf"

    attendance_list = {}
    data = {}

    for file in files:
        if file[-3:] == 'pdf':
            readFile(file)
        else:
            print("Invalid file: " + file)

    attendance_list_desc = sortAttendance(attendance_list, reverse=True)
    attendance_list_asc = sortAttendance(attendance_list, reverse=False)
    filtered_data_desc = filterData(attendance_list_desc)
    filtered_data_asc = filterData(attendance_list_asc)
    generateOutput(filtered_data_desc, filtered_data_asc)