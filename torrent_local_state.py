from typing import Set, List

SID_FLAG_RANGE = 1 << 31


class TorrentLocalState:
    _local_block: Set[int] = set()

    # file_index = list()

    @property
    def local_block(self) -> set[int]:
        return self._local_block

    @property
    def packed_local_block(self) -> List[int]:
        return self.pack_seq_ids(self.local_block)

    @staticmethod
    def match_block(owned: Set[int], offered: Set[int]):
        return offered.difference(owned)

    @staticmethod
    def pack_seq_ids(ids: Set[int]) -> List[int]:
        """
        压缩seq_ids
        :param ids:
        :return:
        """
        iids = ids.copy()
        ret = list()
        range_start = 0
        max_ids = max(iids)
        for i in range(1, max_ids + 1):
            if i not in ids:
                if range_start == 0:
                    continue
                else:
                    if range_start == i - 1:
                        ret.append(range_start)
                    else:
                        # has range, start from range start to i-1
                        ret.append(range_start | SID_FLAG_RANGE)
                        ret.append((i - 1) | SID_FLAG_RANGE)
                    range_start = 0
            else:
                # contains i
                if i == max_ids:
                    if range_start == 0:
                        ret.append(i)
                    else:
                        ret.append(range_start | SID_FLAG_RANGE)
                        ret.append(i | SID_FLAG_RANGE)
                    break
                if range_start != 0:
                    continue
                    # already in a range, try to extend
                else:
                    range_start = i
                    continue

        return ret

    @staticmethod
    def unpack_seq_ids(ids: List[int]) -> Set[int]:
        """
        解压缩 Seq ids
        :param ids:
        :return:
        """
        ret = set()
        range_start = 0
        for i in ids:
            if i & SID_FLAG_RANGE == SID_FLAG_RANGE:
                i = i & (SID_FLAG_RANGE - 1)
                if range_start == 0:
                    range_start = i
                    continue
                else:
                    # end of a range
                    for ii in range(range_start, i + 1):
                        ret.add(ii)
                    range_start = 0
            else:
                ret.add(i)
        return ret