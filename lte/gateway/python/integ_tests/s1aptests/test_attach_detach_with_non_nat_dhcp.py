"""
Copyright 2022 The Magma Authors.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import time
import unittest

import s1ap_types
from integ_tests.s1aptests import s1ap_wrapper
from s1ap_utils import MagmadUtil


class TestAttachDetachWithNonNatDhcp(unittest.TestCase):

    def setUp(self):
        """Initialize before test case execution"""
        self.magma_utils = MagmadUtil(None)

        self.magma_utils.enable_dhcp_config()
        self._s1ap_wrapper = s1ap_wrapper.TestWrapper()
        self.magma_utils.disable_nat()

    def tearDown(self):
        """Cleanup after test case execution"""
        self.magma_utils.disable_dhcp_config()
        self.magma_utils.enable_nat()
        self._s1ap_wrapper.cleanup()

    def test_attach_detach_with_non_nat_dhcp(self):
        """ Basic attach/detach test with two UEs and DHCP"""
        num_ues = 2
        detach_type = [
            s1ap_types.ueDetachType_t.UE_NORMAL_DETACH.value,
            s1ap_types.ueDetachType_t.UE_SWITCHOFF_DETACH.value,
        ]
        wait_for_s1 = [True, False]
        self._s1ap_wrapper.configUEDevice(num_ues)

        for i in range(num_ues):
            req = self._s1ap_wrapper.ue_req
            print(
                "************************* Running End to End attach for ",
                "UE id ", req.ue_id,
            )
            # Now actually complete the attach
            self._s1ap_wrapper._s1_util.attach(
                req.ue_id, s1ap_types.tfwCmd.UE_END_TO_END_ATTACH_REQUEST,
                s1ap_types.tfwCmd.UE_ATTACH_ACCEPT_IND,
                s1ap_types.ueAttachAccept_t,
            )

            # Wait on EMM Information from MME
            self._s1ap_wrapper._s1_util.receive_emm_info()
            print(
                "************************* Running UE detach for UE id ",
                req.ue_id,
            )
            # Now detach the UE
            self._s1ap_wrapper.s1_util.detach(
                req.ue_id, detach_type[i], wait_for_s1[i],
            )

        wait_interval = 5
        max_iterations = 12
        print(f"Waiting for a maximum of {max_iterations * wait_interval} seconds for IPs to be released")
        for i in range(max_iterations):
            keys, _, _, _ = self.magma_utils.get_redis_state()
            if len(keys) == 0:
                print(f"  All IPs released after {i * wait_interval} seconds")
                break
            print(f"  {len(keys)} IP(s) still in use after {i * wait_interval} seconds")
            time.sleep(wait_interval)
            if i == max_iterations - 1:
                assert False, f"IPs not released after {max_iterations * wait_interval} seconds"


if __name__ == "__main__":
    unittest.main()
