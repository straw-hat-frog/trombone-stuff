import re
from django.utils.timezone import datetime
from django.http import HttpResponse
from django.http import FileResponse
from scipy.io.wavfile import write
from io import BytesIO
from hello import wf_generator, info_fetcher

# handles sending info back and forth from the user
# including:
#   - input cleaning and validation
#   - encoding various stuff correctly

# print("http://127.0.0.1:8000/hello/VSCode")
max_dur = 60 # maximum song duration is 60 seconds
key_lifetime = 1800 # maximum lifetime of a session is 30 minutes of inactivity
minimum_dur = 3 * wf_generator.ramp_time # minimum note duration to ensure appropriate ramping

def add_freq(request, frequency):
    # clean inputs
    match_object = re.match("^\\d+$", frequency)

    if match_object:
        clean_freq = int(frequency)
        clean_freq = max(0, clean_freq)
        # TODO: make sure number is within appropriate range (ie positive)
        # if freq = 0, note is silence

        # retrieve current user data from redis
        ip_address = info_fetcher.getIPaddress(request)
        userInfo = info_fetcher.getUserInfo(ip_address)

        
        # test if you're allowed to add frequency
        # ie: begin a whole new input - new frequency not added yet
        if(len(userInfo["duration"]) == len(userInfo["frequency"])):
            # push new user info to redis
            info_fetcher.setUserInfo(ip_address, 
                                     userInfo["frequency"] + [clean_freq],  # append new frequency
                                     userInfo["duration"],
                                     userInfo["slide-duration"] + [0],      # add new info. by default, no slide
                                     key_lifetime)
            
            # TODO: redirect to appropriate page (frequency picker? note duration picker?)
            #return HttpResponse(f"added new note! {info_fetcher.getUserInfo(ip_address)}")
            return HttpResponse(status=204)
        else: # if user hasn't finished setting note duration
            # TODO: redirect to appropriate error page
            return HttpResponse(status=204)
    else: # if inputs are not clean
        return HttpResponse(status=204)


def add_dur(request, duration):
    # clean inputs
    match_object = re.match("^\\d+$", duration)

    if match_object:
        clean_dur = int(duration)/1000
        clean_dur = max(minimum_dur, clean_dur)

        # retrieve current user data from redis
        ip_address = info_fetcher.getIPaddress(request)
        userInfo = info_fetcher.getUserInfo(ip_address)

        if( # test if you're allowed to add duration
            len(userInfo["duration"]) == len(userInfo["frequency"]) - 1 # frequency already added but duration not
            and (sum(userInfo["slide-duration"])        # the new duration isn't too long
                 + sum(userInfo["duration"]) 
                 + clean_dur <= max_dur)
            ):

            # push new user info to redis
            info_fetcher.setUserInfo(ip_address, 
                                     userInfo["frequency"],
                                     userInfo["duration"] + [clean_dur], # append new duration
                                     userInfo["slide-duration"],
                                     key_lifetime)
            
            # TODO: redirect to appropriate page (frequency picker? note duration picker?)
            #return HttpResponse(f"added current note's duration! {info_fetcher.getUserInfo(ip_address)}")
            return HttpResponse(status=204)
        else: # if note duration failed to pass muster in some way
            # TODO: redirect to appropriate error page (duration too long? already added duration?)
            return HttpResponse(status=204)
    else: # if inputs are not clean
        return HttpResponse(status=204)


def add_slide(request, slide_duration):
    # clean inputs
    match_object = re.match("^\\d+$", slide_duration)

    if match_object:
        clean_slide_dur = int(slide_duration)/1000
        clean_slide_dur = max(minimum_dur, clean_slide_dur)

        # retrieve current user data from redis
        ip_address = info_fetcher.getIPaddress(request)
        userInfo = info_fetcher.getUserInfo(ip_address)

        if( # test if you're allowed to add slide duration
            len(userInfo["frequency"]) == len(userInfo["slide-duration"]) # data aren't broken in weird ways
            and len(userInfo["frequency"]) > 1          # there's a previous note to slide from
            and not userInfo["frequency"][-1] == 0      # the previous note isn't silence
            and userInfo["slide-duration"][-1] == 0     # the user hasn't already set a slide duration
            # and userInfo["slide duration"][-2] == 0     # do not allow two slides in a row :(
            and (sum(userInfo["slide-duration"])        # the new duration isn't too long
                 + sum(userInfo["duration"]) 
                 + clean_slide_dur <= max_dur)  
            ):
            # replace final "0 s slide" with new slide duration
            new_slide_dur = userInfo["slide-duration"]
            new_slide_dur[-1] = clean_slide_dur

            # push new user info to redis
            info_fetcher.setUserInfo(ip_address, 
                                     userInfo["frequency"],
                                     userInfo["duration"],
                                     new_slide_dur,
                                     key_lifetime)
            
            # TODO: redirect to appropriate page (frequency picker? note duration picker?)
            #return HttpResponse(f'added slide to current note! {info_fetcher.getUserInfo(ip_address)}')
            return HttpResponse(status=204)
        else: # if slide duration failed to pass muster in some way
            # TODO: redirect to appropriate error page (slide too long? no previous note?)
            return HttpResponse(status=204)
    else: # if inputs are not clean
        return HttpResponse(status=204)


def clear_data(request):
    ip_address = info_fetcher.getIPaddress(request)
    info_fetcher.clearUserInfo(ip_address)
    return HttpResponse(status=204)

# build the actual song from saved user data (for audio src html element)
def fetch_song(request):
    # retrieve current user data from redis
    ip_address = info_fetcher.getIPaddress(request)
    userInfo = info_fetcher.getUserInfo(ip_address)

    # create waveform (as numpy array)
    stimulus = wf_generator.build_user_song(userInfo["frequency"], userInfo["duration"], userInfo["slide-duration"])

    # write stimulus to a format i can send
    bytes_wav = bytes()
    byte_io = BytesIO(bytes_wav)

    write(byte_io, wf_generator.fs, stimulus)

    # prepare and send the .wav file!!
    byte_io.seek(0)
    response = FileResponse(byte_io, as_attachment=True, filename='trombone-song.wav')
    return response
    