"""A matching board subset cannot conceal changed electrical job inputs."""
from copy import deepcopy
import unittest
from bind_result_applicability import JOB_KEYS,compare_jobs
from copper_fem import Refused


class ApplicabilityTests(unittest.TestCase):
    def test_every_operational_job_category_is_compared(self):
        original={key:{'frozen_value':key}for key in JOB_KEYS}
        self.assertTrue(all(row['identical']for row in compare_jobs(original,deepcopy(original)).values()))
        for key in JOB_KEYS:
            with self.subTest(key=key):
                changed=deepcopy(original);changed[key]={'changed':True}
                with self.assertRaises(Refused):compare_jobs(original,changed)

    def test_descriptive_source_metadata_does_not_change_the_compared_job(self):
        original={key:[]for key in JOB_KEYS};other=deepcopy(original)
        original['source_stage']='original source';other['source_stage']='compared source'
        self.assertTrue(all(row['identical']for row in compare_jobs(original,other).values()))


if __name__=='__main__':unittest.main(verbosity=2)
