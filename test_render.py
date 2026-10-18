"""Small deterministic regression checks; no full video encode required."""
import unittest
import numpy as np
from render import frame_at, SHOTS, FPS

class FilmTests(unittest.TestCase):
    def test_continuous_one_minute_timeline(self):
        self.assertEqual(SHOTS[0][0],0)
        self.assertEqual(SHOTS[-1][1],60)
        for first,second in zip(SHOTS,SHOTS[1:]):
            self.assertEqual(first[1],second[0])
        self.assertEqual(60*FPS,1440)

    def test_motion_in_center_not_just_titles(self):
        # Compare the central artwork region, excluding titles and progress bar.
        for t in [4,15,20,30,41,51,57]:
            with self.subTest(time=t):
                a=np.asarray(frame_at(t)).astype(float)[150:740,190:890]
                b=np.asarray(frame_at(t+.5)).astype(float)[150:740,190:890]
                fraction=np.mean(np.max(np.abs(a-b),axis=2)>8)
                # Thin-line diagram scenes are deliberately sparse; require >0.5%
                # of the central pixels to change, not merely title movement.
                self.assertGreater(fraction,.005)

    def test_format_and_boundaries(self):
        for t in [0,.5,3,7,13,19,24,28,35,40,45,50,56,59.99]:
            image=frame_at(t)
            self.assertEqual(image.size,(1080,1080))
            self.assertEqual(image.mode,'RGB')

if __name__=='__main__':unittest.main()
