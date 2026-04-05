import mediapipe as mp
print(dir(mp))
try:
    import mediapipe.python as mpp
    print("MPP dir:", dir(mpp))
except:
    print("No mpp")
