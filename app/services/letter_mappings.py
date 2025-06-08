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
            ("Map 1", self.abgd_map_1),
            ("Map 2", self.abgd_map_2),
            ("Map 3", self.abgd_map_3),
            ("Map 4", self.abgd_map_4)
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
            results.append((self.abgd_map_4[ch], "Map 4"))
        
        # Maps 5-8
        results.extend(self.get_grouped_mapped(ch, self.abgd_map_5, "Map 5"))
        results.extend(self.get_grouped_mapped(ch, self.abgd_map_6, "Map 6"))
        results.extend(self.get_grouped_mapped(ch, self.abgd_map_7, "Map 7", apply_normalization=True))
        results.extend(self.get_grouped_mapped(ch, self.abgd_map_8, "Map 8"))
        
        # Original character
        results.append((ch, "Original"))
        
        return list(set(results))
    
    def generate_all_variants(self, phrase: str, max_variants: int = 10000) -> List[Tuple[str, List[str]]]:
        """Generate all possible variants of a phrase using letter mappings.
        
        Args:
            phrase: The phrase to generate variants for
            max_variants: Maximum number of variants to generate (default 10000)
        """
        letter_options = []
        
        for ch in phrase:
            if ch == ' ':
                letter_options.append([(' ', 'Original')])
            else:
                letter_options.append(self.get_possible_conversions(ch))
        
        # Calculate total possible combinations
        total_possible = 1
        for options in letter_options:
            total_possible *= len(options)
        
        # If total combinations exceed max_variants, use a smarter approach
        if total_possible > max_variants:
            return self._generate_limited_variants(phrase, letter_options, max_variants)
        
        # Generate all combinations (only for small phrases)
        variants = []
        for combo in itertools.product(*letter_options):
            variant_text = "".join([ltr for ltr, _ in combo])
            sources = [src for _, src in combo]
            variants.append((variant_text, sources))
        
        return variants
    
    def _generate_limited_variants(self, phrase: str, letter_options: List[List[Tuple[str, str]]], 
                                  max_variants: int) -> List[Tuple[str, List[str]]]:
        """Generate a limited set of high-quality variants for long phrases."""
        import random
        variants = []
        seen_variants = set()
        
        # Always include the original
        original_variant = "".join([opt[0][0] for opt in letter_options])
        original_sources = ["Original"] * len(phrase.replace(' ', ''))
        variants.append((original_variant, original_sources))
        seen_variants.add(original_variant)
        
        # Strategy 1: Include single-character changes (most likely to find matches)
        for i, ch_options in enumerate(letter_options):
            if ch_options[0][0] == ' ':
                continue
            
            for alt_char, source in ch_options[1:]:  # Skip original
                if len(variants) >= max_variants:
                    break
                    
                # Create variant with single character changed
                variant_chars = [opt[0][0] for opt in letter_options]
                variant_sources = ["Original"] * len(letter_options)
                variant_chars[i] = alt_char
                variant_sources[i] = source
                
                variant_text = "".join(variant_chars)
                if variant_text not in seen_variants:
                    variants.append((variant_text, variant_sources))
                    seen_variants.add(variant_text)
        
        # Strategy 2: Include variants from each map type
        for map_name in ["Map 1", "Map 2", "Map 3", "Map 4", "Map 5", "Map 6", "Map 7", "Map 8"]:
            if len(variants) >= max_variants:
                break
                
            variant_chars = []
            variant_sources = []
            
            for ch_options in letter_options:
                # Find a conversion from the current map
                found = False
                for char, source in ch_options:
                    if source == map_name:
                        variant_chars.append(char)
                        variant_sources.append(source)
                        found = True
                        break
                
                if not found:
                    # Use original if no mapping exists
                    variant_chars.append(ch_options[0][0])
                    variant_sources.append("Original")
            
            variant_text = "".join(variant_chars)
            if variant_text not in seen_variants:
                variants.append((variant_text, variant_sources))
                seen_variants.add(variant_text)
        
        # Strategy 3: Random sampling for remaining slots
        attempts = 0
        while len(variants) < max_variants and attempts < max_variants * 2:
            attempts += 1
            
            # Generate a random variant
            variant_chars = []
            variant_sources = []
            
            for ch_options in letter_options:
                char, source = random.choice(ch_options)
                variant_chars.append(char)
                variant_sources.append(source)
            
            variant_text = "".join(variant_chars)
            if variant_text not in seen_variants:
                variants.append((variant_text, variant_sources))
                seen_variants.add(variant_text)
        
        return variants
