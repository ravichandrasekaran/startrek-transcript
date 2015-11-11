"""Data download and munging from Star Trek TNG transcripts"""

from bs4 import BeautifulSoup
import bs4
import nltk

import re
import time
import requests
import os
import pprint as pp
import collections
import logging
import numpy as np
import pandas as pd

_LineRecord = collections.namedtuple('_LineRecord', \
    ['episode', 'location', 'line_num', 'directions', 'speaker', \
    'blocking', 'spoken'])

pp = pp.PrettyPrinter(width=300)

TNG_BASE_URL = "http://www.chakoteya.net/NextGen"
TNG_EPISODE_URL = TNG_BASE_URL + "/episodes.htm"
LOCAL_BASE_PATH = "~/code/tng"
LOCAL_EPISODE_PATH = LOCAL_BASE_PATH + "/downloads"
LOCAL_FILE_PREFIX = "tng_"
EPISODE_LIST_LOCAL = "tng_index.html"
ERROR_COUNT = 0

def create_episode_index():
    """ Using global index file, extract set of links and info (episode number,
        URL) from index page. """

    soup = BeautifulSoup(open(EPISODE_LIST_LOCAL), "html.parser")
    episode_links = soup.find_all("a")

    episodes = []

    for i in episode_links:
        epi = {}

        if i.attrs["href"] == "../index.html" \
            or i.attrs["href"] == "http://www.cbs.com":
            # TODO - replace this hack with parent identification in table.
            break

        epi['href'] = TNG_BASE_URL + "/" + i.attrs["href"]
        info = i.find_parents("td")[0].find_next_siblings("td")

        mat = re.search(r"(\d+)", info[0].string)
        if mat:
            epi['num'] = int(mat.group(1))

        for child in info[1].children:
            mat = re.search(r"(\d+)\W+(\w{3})\D*(\d+)", child.string)
            if mat:
                date_string = mat.group(1) + " " + mat.group(2) + " " + mat.group(3)
                epi['airdate'] = time.strptime(date_string, "%d %b %Y")

        episodes.append(epi)


    return episodes


def capture_episode(str_url, episode_num):
    """ Given the URL (str_url) to an individual episode, pull down the HTML
        source to current working directory. Filename is constructed using the
        episode number (episode_num), like tng_33.html. """

    resp = requests.get(str_url)
    script = resp.text
    script = re.sub(r"<br>|<rb>|<nbr>|<nr>", r"<br />", script, \
        flags=re.IGNORECASE)
    # doctoring the HTML to deal with bad effects from BS4 <br> expansion

    epi_filename = LOCAL_FILE_PREFIX + str(episode_num) + ".html"
    f = open(epi_filename, 'w')
    f.write(script)
    f.close()

    return


def capture_all_episodes(episodes):
    """ Given an episode index, loop through and capture each episode locally.
    Use capture_episode() internally to handle the HTML and file storage. """

    # TODO - pretty empty here, may consolidate

    for i in episodes:
        capture_episode(i['href'], i['num'])

    return


def extract_episode(episode_num):
    """ Given an episode number, grab the local contents (assumes successful
        capture_episode(), and in appropriate working directory). Start
        parsing, using the table and p structure. """

    lines = []
    epi_filename = LOCAL_FILE_PREFIX + str(episode_num) + ".html"
    f = open(epi_filename, 'r')
    text = f.read()
    text = re.sub('<a[^>]+>', '', text)
    text = re.sub(r'</a>', '', text)
    text = re.sub('<o[^>]+>', '', text)
    text = re.sub(r'</o>', '', text)
    soup = BeautifulSoup(text, "html.parser")
    f.close()
    for match in soup.findAll('i'):
        match.extract()
    td_container = soup.find("td")
    td_container.font.extract()

    for block in td_container.children:
        if isinstance(block, bs4.element.NavigableString):
            # Empty spaces between </p> and <p> tags.
            pass
        elif isinstance(block.contents[0], bs4.element.NavigableString):
            # Interior content unenclosed by <p> tags, sometimes logs.
            text = block.contents[0]
            text = re.sub('\n', ' ', text).strip()
            # Including a list wrapper to match text.
            lines.append([text])
        else:
            # Assumed <p> bs4 block.
            content_block = block.contents[0]
            paragraph = [re.sub('\n', ' ', str(lin).strip()) \
                for lin in content_block \
                if str(lin).strip() != '<br/>' and str(lin).strip()]
            lines.append(paragraph)

    # TODO - Should we preserve the block structure? Flattened here.
    lines = [lin for block in lines for lin in block]
    return lines



def process_lines(lines, ep_num):


    scene_marker = re.compile('<b>\[?(.*?)\]?</b>')
    stage_direction_marker = re.compile('\((.*?)\)')
    blocking_marker = re.compile('\[(.*?)\]')
    forgotten_colon = re.compile('([A-Z\s-])+\s+\[.*?\]')

    linrecs = []
    current_location = ''
    previous = ('', '')

    for idx, lin in enumerate(lines):

        if len(lin) < 2:
            continue

        # Tidy up enclosures
        if lin[0] == '[' and lin[-1] == ']':
            lin = '<b>' + lin + '</b>'
        if '(' in lin and ')' not in lin:
            lin = lin + ')'
        if ')' in lin and '(' not in lin:
            lin = '(' + lin
        lin = re.sub('\[(.*?)[\[}]', r'[\1]', lin)
        lin = re.sub('[\]{](.*?)\]', r'[\1]', lin)
        lin = re.sub('\((.*?)\(', r'(\1)', lin)
        lin = re.sub('\)(.*?)\)', r'(\1)', lin)
        if forgotten_colon.match(lin) and ':' not in lin:
            lin = re.sub('\]', r']:', lin, count=1)
        if ':' not in lin and re.match('[A-Z-\']{3,}', lin):
            mat = re.match('([A-Z-\']{3,})', lin)
            sp = mat.group(1)
            lin = re.sub(sp, sp+':', lin)

        if '<b>' in lin:
            locations = scene_marker.findall(lin)
            if locations:
                current_location = locations[0].strip()
            else:
                logging.warn('Unable to parse location %s', lin)
            continue


        stage_direction = ''
        stage_directions = stage_direction_marker.findall(lin)
        if stage_directions:
            stage_direction = stage_directions[0]
        lin = stage_direction_marker.sub('', lin)

        speaker = ''
        blocking = ''
        spoken = ''
        location = ''

        if ':' in lin:
            speaker_info, spoken = re.split(':', lin, maxsplit=1)
            blockings = blocking_marker.findall(speaker_info)
            if blockings:
                blocking = blockings[0].strip()
            speaker = blocking_marker.sub('', speaker_info).strip()
            speaker_set = re.findall('([A-Z].*)', speaker)
            if speaker_set:
                speaker = speaker_set[0]
            spoken = re.sub('<font>', '', spoken)
            spoken = spoken.strip()

        if not speaker and not stage_direction and len(lin.strip()) > 2:
            if re.search(r'(\blog\b|\bsupplemental\b|\bstardate\b)', lin.lower()):
                spoken = lin.strip()
                stage_direction = 'log'
            else:
                location = previous[0]
                speaker = previous[1]
                spoken = lin.strip()

        previous = (location, speaker)
        linrec = _LineRecord(episode=ep_num, location=current_location, \
            line_num=idx, directions=stage_direction, speaker=speaker, \
            blocking=blocking, spoken=spoken)
        linrecs.append(linrec)

    return linrecs



# logs
# loggers = re.findall('^(.*?)\slo', lin.lower())
# if len(loggers) > 0:
#     logs.append(loggers[0])
# {'medical', 'second officers personal', "chief engineer's",
# 'counsellor deanna troi, personal', "second officer's", 'military',
# 'lieutenant worf, personal', 'doctor beverly crusher, personal',
# "chief medical officer's", "first officer's personal",
# "second officer's science", "second officer's personal", "acting captain's",
# "first officer's", "ship's", "medical officer's", "captain's",
# "bridge officer's", 'personal', 'enterprise', "captain's personal"}

def summary_stats(linrecs):

    spoken = [linrec for linrec in linrecs if linrec.speaker]
    speaker_summ = collections.Counter([linrec.speaker for linrec in linrecs])
    main_speakers = [speaker for (speaker, cnt) in speaker_summ.items() \
        if cnt > len(spoken) * .01 and speaker]

    for i in main_speakers:
        total_lines = [lr.spoken for lr in linrecs if lr.speaker == i]
        questions = [lr.spoken for lr in linrecs \
            if lr.speaker == i and '?' in lr.spoken]
        print('For {}: {} questions of {} lines ({}%).'.format(i, \
            len(questions), len(total_lines), \
            round((len(questions) / len(total_lines))*100,2)))
        # print('\n\n' + i)
        # pp.pprint(questions[:10])


    p = pd.DataFrame.from_records(linrecs, columns=linrecs[0]._fields)
    print('\n\n\nData frame: ' + str(len(p)))
    p['question'] = ('?' in p['spoken'])
    questions = p[p['question']]
    print(questions[:50])

    #computer_lines = [(lr.speaker, lr.spoken) for lr in linrecs if re.search('Computer[,:]', lr.spoken)]
    computer_lines = [(lr.speaker, lr.blocking, lr.spoken) for lr in linrecs if re.search('[Ee]arl\s[Gg]r[ea]y[,:]', lr.spoken)]
    pp.pprint(computer_lines)
    balance = []
    balance_words = []
    balance_wl = []
    for (speaker, computer_line) in computer_lines:
        balance += re.findall('Computer[,:]([^!?.]+[!?.])', computer_line)
    for i in balance:
        balance_words.append(nltk.word_tokenize(i))
        balance_wl += nltk.word_tokenize(i)

    stopwords = nltk.corpus.stopwords.words('english')
    balance_wl = [w for w in balance_wl if w not in stopwords]
    fd = nltk.FreqDist(balance_wl)
    print(fd.most_common(50))
    pp.pprint(sorted(balance_words))
    # blocking_summ = collections.Counter([linrec.blocking \
    #     for linrec in linrecs])
    # print(blocking_summ)


    repetitive_questions = [lr.spoken for lr in linrecs if lr.speaker == 'PICARD' and re.findall('\?.*?\?', lr.spoken)]
    print('\n\nLength of double questions. ' + str(len(repetitive_questions)))

    pp.pprint(repetitive_questions)
    strong_modals = ['can', 'may',  'shall',  'will', 'must']
    weak_modals = ['could', 'might', 'should', 'would', 'ought']
    picard_quest = [lr.spoken for lr in linrecs for mod in strong_modals if lr.speaker == 'PICARD' and '?' in lr.spoken and mod in lr.spoken]
    print('\n\nLength of strong modals '+ str(len(picard_quest)))

    picard_weak = [lr.spoken for lr in linrecs for mod in weak_modals if lr.speaker == 'PICARD' and '?' in lr.spoken and mod in lr.spoken]
    print('\n\nLength of weak modals '+ str(len(picard_weak)))

    pp.pprint((picard_weak)[:100])



if __name__ == "__main__":

    EPISODE_LIST = []
    EPISODE_LIST = create_episode_index()
    lines = []
    linrecs = []
    os.chdir(os.path.expanduser(LOCAL_EPISODE_PATH))

    for ep in EPISODE_LIST:
        lines = extract_episode(ep['num'])
        linrecs = linrecs + process_lines(lines, ep['num'])
    summary_stats(linrecs)
    #capture_all_episodes(EPISODE_LIST)

    # print(ERROR_COUNT)

    # lines = extract_episode(ep['num'])
    # process_episode(lines)
