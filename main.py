"""
The main program that is used to play the game.

:author: `Dana Ladon <dana.ladon@ens.fr>`_

:date:  2019, december

.. testsetup::*

        from main import *

"""
import cv2
import numpy as np
import pygame

HEAD_COLOR = (255, 255, 0)
EYES_COLOR = ((0, 255, 255), (255, 0, 255))
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (127, 127, 127)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)


def detect_eyes(img, classifier):
    """
    Function that detect the eyes, so only in the first half of the face and return the right vs left eye.

    :param img: The image where the eyes should be located
    :type img: numpy.ndarray
    :param classifier: The classifier used to detect the eyes
    :type classifier: cv2.CascadeClassifier
    :returns: The right eye and the left eye
    :rtype: numpy.ndarray|None

    :UC: None

    .. doctest::

        >>> from main import *
        >>> import cv2
        >>> from numpy import ndarray
        >>> img = cv2.imread("data/test.jpeg")
        >>> face_cascade = cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')
        >>> eye_cascade = cv2.CascadeClassifier('data/haarcascade_eye.xml')
        >>> face = detect_face(img, face_cascade)
        >>> left_eye, right_eye = detect_eyes(face, eye_cascade)
        >>> # In this case it is true but might be None also
        >>> isinstance(left_eye, ndarray) and isinstance(right_eye, ndarray)
        True
    """
    gray_frames = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    eyes = classifier.detectMultiScale(gray_frames, 1.3, 5)
    height = np.size(img, 0)  # get the width and height of the face image
    width = np.size(img, 1)
    left_eye, right_eye = None, None  # In case no eyes are detected...
    for (x, y, w, h) in eyes:
        if y > height / 2:  # pass if the eye is not on the top of the face
            pass

        eyecenter = x + w / 2  # get the eye center
        if eyecenter < width * 0.5:
            left_eye = img[y:y + h, x:x + w]
        else:
            right_eye = img[y:y + h, x:x + w]

    return left_eye, right_eye


def detect_face(img, classifier):
    """
    Function that detect the biggest face on the image and returns it.

    :param img: The image where the face should be located
    :type img: numpy.ndarray
    :param classifier: The classifier used to detect the face
    :type classifier: cv2.CascadeClassifier
    :returns: The image cropped around the face
    :rtype: numpy.ndarray|None

    :UC: None

    .. doctest::

        >>> import cv2
        >>> from numpy import ndarray
        >>> img = cv2.imread("data/test.jpeg")
        >>> face_cascade = cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')
        >>> face = detect_face(img, face_cascade)
        >>> isinstance(face, ndarray)
        True
    """
    gray_frame = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    coords = classifier.detectMultiScale(gray_frame, 1.3, 5)
    if len(coords) == 0:
        return None  # No faces detected
    biggest = (0, 0, 0, 0)
    for i in coords:
        if i[3] > biggest[3]:
            biggest = i  # Largest width is chosen (Could have been width and height combined also)
    x, y, w, h = biggest
    return img[y:y + h, x:x + w]


def cut_eyebrows(img):
    """
    Remove the eyebrows from the eye.

    :param img: One eye where you want to remove the eyebrow from the image
    :type img: numpy.ndarray
    :returns: The image without the eyebrow
    :rtype: numpy.ndarray

    .. doctest::

        >>> from main import *
        >>> import cv2
        >>> from numpy import ndarray
        >>> img = cv2.imread("data/test.jpeg")
        >>> res = cut_eyebrows(img)
        >>> height, width = img.shape[:2]
        >>> res_height, res_width = res.shape[:2]
        >>> res_height == 3*height // 4
        True
        >>> width == res_width
        True
        >>> isinstance(img, ndarray)
        True
        >>> isinstance(res, ndarray)
        True
    """
    height, width = img.shape[:2]
    eyebrow_h = int(height / 4)
    return img[eyebrow_h:height, 0:width]


def blob_process(img, detector, threshold):
    """
    Detect the blob of the eye.

    :param img: The eye image without eyebrows
    :type img: numpy.ndarray
    :param detector: The detector object used to find the blob
    :type detector: cv2.SimpleBlobDetector
    :param threshold: The threshold we use to darken or lighten the black and white image
                      (a threshold of 10, would convert any pixel below 10 to  0 and above 10 to 255)
    :type threshold: int
    :returns: A list of keypoints or None if not detected
    :rtype: list|None

    :UC: 0 <= threshold <= 255

    .. doctest::

        >>> from main import *
        >>> import cv2
        >>> from numpy import ndarray
        >>> detector_params = cv2.SimpleBlobDetector_Params()
        >>> detector_params.filterByArea = True
        >>> detector_params.maxArea = 1500
        >>> detector_params.filterByConvexity = False
        >>> detector_params.filterByInertia = False
        >>> detector = cv2.SimpleBlobDetector_create(detector_params)
        >>> img = cv2.imread("data/test.jpeg")
        >>> face_cascade = cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')
        >>> eye_cascade = cv2.CascadeClassifier('data/haarcascade_eye.xml')
        >>> face = detect_face(img, face_cascade)
        >>> left_eye, right_eye = detect_eyes(face, eye_cascade)
        >>> left_eye = cut_eyebrows(left_eye)
        >>> keypoints = blob_process(left_eye, detector, 42)
        >>> isinstance(keypoints, list)
        True
        >>> isinstance(keypoints[0], cv2.KeyPoint)
        True
    """
    assert 0 <= threshold <= 255, f"Threshold is too high({threshold}). It should be between 0 and 255 "
    gray_frame = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    retval, img = cv2.threshold(gray_frame, threshold, 255, cv2.THRESH_BINARY)
    img = cv2.erode(img, None, iterations=2)  # 1
    img = cv2.dilate(img, None, iterations=4)  # 2
    img = cv2.medianBlur(img, 5)  # 3
    keypoints = detector.detect(img)
    return keypoints


def draw_cross(screen, centerx, centery, width, height, crossthickness=5, color=BLUE):
    """
    A simple function to draw a cross on the screen

    :param screen: The screen where we want to do the cross
    :type screen: pygame.Surface
    :param centerx: The x position of the center of the cross
    :type centerx: int
    :param centery: The y position of the center of the cross
    :type centery: int
    :param width: the width of the cross
    :type width: int
    :param height: the height of the cross
    :type height: int
    :param crossthickness: the thickness of the lines of the cross (which are here rectangles in fact)
    :type crossthickness: int
    :param color: A color tuple that contains 3 values between 0 and 255
    :type color: tuple

    :UC: None

    """
    pygame.draw.rect(screen, color,
                     (centerx - crossthickness // 2, centery - height // 2, crossthickness, height))

    pygame.draw.rect(screen, color,
                     (centerx - width // 2, centery - crossthickness // 2, width, crossthickness))


def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    screen.fill(WHITE)
    W, H = pygame.display.Info().current_w, pygame.display.Info().current_h

    # display the backbuffer
    pygame.display.flip()

    # First need the classifiers
    face_cascade = cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier('data/haarcascade_eye.xml')

    # Blob detector
    detector_params = cv2.SimpleBlobDetector_Params()
    detector_params.filterByArea = True
    detector_params.maxArea = 1500
    detector_params.filterByConvexity = False
    detector_params.filterByInertia = False
    detector = cv2.SimpleBlobDetector_create(detector_params)

    cap = cv2.VideoCapture(0)
    cv2.namedWindow('jeu')
    cv2.createTrackbar('threshold', 'jeu', 0, 255, lambda x: 0)
    eyes_position = dict()  # Dictionnary to store the eyes positions (top, middle, bottom, right and left)

    step = 0  # Initialization variable (where the user has to look or if the game starts)
    keys = ['middle', 'top', 'right', 'bottom', 'left']
    capture_position = [False, False]

    while True:
        ret, frame = cap.read()
        face_frame = detect_face(frame, face_cascade)

        if face_frame is not None:
            left_eye, right_eye = detect_eyes(face_frame, eye_cascade)
            threshold = cv2.getTrackbarPos('threshold', 'jeu')

            if left_eye is not None:
                left_eye = cut_eyebrows(left_eye)
                keypoints = blob_process(left_eye, detector, threshold)

                cv2.drawKeypoints(left_eye, keypoints, left_eye, (0, 0, 255),
                                  cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
                if capture_position[0]:
                    keyname = keys[step - 1]
                    pos = eyes_position.get(keyname, [])
                    pos.append(keypoints[0].pt)  # Adding the left eye position
                    eyes_position[keyname] = pos
                    capture_position[0] = False

            if right_eye is not None:
                right_eye = cut_eyebrows(right_eye)
                keypoints = blob_process(right_eye, detector, threshold)
                cv2.drawKeypoints(right_eye, keypoints, right_eye, (0, 0, 255),
                                  cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
                if capture_position[1]:
                    keyname = keys[step - 1]
                    pos = eyes_position.get(keyname, [])
                    pos.append(keypoints[0].pt)  # Adding the left eye position
                    eyes_position[keyname] = pos
                    capture_position[1] = False

        cv2.imshow('jeu', frame)

        # Analysis done pygame part

        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                cv2.destroyAllWindows()
                exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.unicode == 'q':
                    cap.release()
                    cv2.destroyAllWindows()
                    print(eyes_position)
                    exit(0)
                if event.key == pygame.K_SPACE:
                    step += 1
                    capture_position = [True, True]  # Left eye and right eye positions must be captured

        if not any(capture_position):
            if step == 0:
                # Middle cross
                draw_cross(screen, W // 2, H // 2, 50, 50)
            elif step == 1:
                # Top cross
                draw_cross(screen, W // 2, H // 10, 50, 50)
            elif step == 2:
                # Right cross
                draw_cross(screen, 9 * W // 10, H // 2, 50, 50)
            elif step == 3:
                # Bottom cross
                draw_cross(screen, W // 2, 9 * H // 10, 50, 50)
            elif step == 4:
                # Left cross
                draw_cross(screen, W // 10, H // 2, 50, 50)

        pygame.display.flip()  # Updating screen

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
