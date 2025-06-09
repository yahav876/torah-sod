"""
Letter mapping configurations for Torah search
"""
import itertools
from typing import List, Tuple, Dict


class LetterMappings:
    """Manages Hebrew letter mappings for Torah search."""
    
    def __init__(self):
        # Initialize all mapping dictionaries
        self.abgd_map_1 = {
            'א': 'ב', 'ב': 'א', 'ג': 'ד', 'ד': 'ג', 'ה': 'ו', 'ו': 'ה',
            'ז': 'ח', 'ח': 'ז', 'ט': 'י', 'י': 'ט', 'כ': 'ל', 'ל': 'כ',
            'מ': 'נ', 'נ': 'מ', 'ס': 'ע', 'ע': 'ס', 'פ': 'צ', 'צ': 'פ',
            'ק': 'ר', 'ר': 'ק', 'ש': 'ת', 'ת': 'ש'
        }
        
        self.abgd_map_2 = {
            'א': 'ת', 'ת': 'א', 'ב': 'ש', 'ש': 'ב', 'ג': 'ר', 'ר': 'ג',
            'ד': 'ק', 'ק': 'ד', 'ה': 'צ', 'צ': 'ה', 'ו': 'פ', 'פ': 'ו',
            'ז': 'ע', 'ע': 'ז', 'ח': 'ס', 'ס': 'ח', 'ט': 'נ', 'נ': 'ט',
            'י': 'מ', 'מ': 'י', 'כ': 'ל', 'ל': 'כ'
        }
        
        self.abgd_map_3 = {
            'א': 'ל', 'ל': 'א', 'ב': 'מ', 'מ': 'ב', 'ג': 'נ', 'נ': 'ג',
            'ד': 'ס', 'ס': 'ד', 'ה': 'ע', 'ע': 'ה', 'ו': 'פ', 'פ': 'ו',
            'ז': 'צ', 'צ': 'ז', 'ח': 'ק', 'ק': 'ח', 'ט': 'ר', 'ר': 'ט',
            'י': 'ש', 'ש': 'י', 'כ': 'ת', 'ת': 'כ'
        }
        
        self.abgd_map_4 = {
            'א': 'ט', 'ט': 'א', 'ב': 'ח', 'ח': 'ב', 'ג': 'ז', 'ז': 'ג',
            'ד': 'ו', 'ו': 'ד', 'צ': 'י', 'ה': 'ה', 'פ': 'כ', 'י': 'צ',
            'ל': 'ע', 'כ': 'פ', 'ס': 'מ', 'ע': 'ל', 'נ': 'נ', 'מ': 'ס',
            'ן': 'ש', 'ץ': 'ק', 'ם': 'ת', 'ף': 'ר',
            'ך': 'ך'  # Keep final letters as is for Map 4
        }
        
        self.abgd_map_5 = [
            ['א', 'י', 'ק'], ['ב', 'כ', 'ר'], ['ג', 'ל', 'ש'],
            ['ד', 'מ', 'ת'], ['ה', 'נ', 'ך'], ['ו', 'ס', 'ם'],
            ['ז', 'ע', 'ן'], ['ח', 'פ', 'ף'], ['ת', 'צ', 'ץ']
        ]
        
        self.abgd_map_6 = [
            ['א', 'ח', 'ס'], ['ב', 'ט', 'ע'], ['ג', 'י', 'פ'],
            ['ד', 'כ', 'צ'], ['ה', 'ל', 'ק'], ['ו', 'מ', 'ר'],
            ['ז', 'נ', 'ש'], ['ז', 'נ', 'ת']
        ]
        
        self.abgd_map_7 = [
            ['א', 'ה', 'ח', 'ע'],
            ['ב', 'ו', 'מ', 'פ'],
            ['ג', 'י', 'כ', 'ק'],
            ['ד', 'ט', 'ל', 'נ', 'ת'],
            ['ז', 'ס', 'ש', 'ר', 'צ']
        ]
        
        self.abgd_map_8 = [['א', 'ה', 'ו', 'י']]
        
        self.final_to_regular = {'ך': 'כ', 'ם': 'מ', 'ן': 'נ', 'ף': 'פ', 'ץ': 'צ'}
        
        self.maps = [
            ("אב״גד", self.abgd_map_1),
            ("את״בש", self.abgd_map_2),
            ("אל״במ", self.abgd_map_3),
            ("את״בח", self.abgd_map_4)
        ]
    
    def get_grouped_mapped(self, ch: str, map_group: List[List[str]], label: str, 
                          apply_normalization: bool = False) -> List[Tuple[str, str]]:
        """Get mapped characters from group-based maps."""
        results = []
        ch_norm = self.final_to_regular.get(ch, ch) if apply_normalization else ch
        
        for group in map_group:
            if ch_norm in group:
                results.extend([(other, label) for other in group if other != ch_norm])
        
        return results
    
    def get_possible_conversions(self, ch: str) -> List[Tuple[str, str]]:
        """Get all possible character conversions for a given Hebrew character."""
        results = []
        norm = self.final_to_regular.get(ch, ch)
        
        # Maps 1-3
        for map_name, mapping in self.maps[:3]:
            if norm in mapping:
                results.append((mapping[norm], map_name))
        
        # Map 4
        if ch in self.abgd_map_4:
            results.append((self.abgd_map_4[ch], "את״בח"))
        
        # Maps 5-8
        results.extend(self.get_grouped_mapped(ch, self.abgd_map_5, "איק-בכר"))
        results.extend(self.get_grouped_mapped(ch, self.abgd_map_6, "אחס-בטע"))
        results.extend(self.get_grouped_mapped(ch, self.abgd_map_7, "מוצאות-הפה", apply_normalization=True))
        results.extend(self.get_grouped_mapped(ch, self.abgd_map_8, "אהוי"))
        
        # Original character
        results.append((ch, "Original"))
        
        return list(set(results))
    
    def generate_all_variants(self, phrase: str) -> List[Tuple[str, List[str]]]:
        """Generate all possible variants of a phrase using letter mappings."""
        letter_options = []
        
        for ch in phrase:
            if ch == ' ':
                letter_options.append([(' ', 'Original')])
            else:
                letter_options.append(self.get_possible_conversions(ch))
        
        # Generate all combinations
        variants = []
        for combo in itertools.product(*letter_options):
            variant_text = "".join([ltr for ltr, _ in combo])
            sources = [src for _, src in combo]
            variants.append((variant_text, sources))
        
        return variants
