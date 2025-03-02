import os
import tempfile
from typing import Dict, Any, Optional, List
import yt_dlp


class YtDlpService:
    """Service for extracting subtitles and chapters from YouTube videos using yt-dlp."""

    def __init__(self):
        """Initialize the YouTube extraction service."""
        # No need to check if yt-dlp is installed since we're importing it directly

    def extract_subtitles(self, url: str, language: str = "en", chapters: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Extract subtitles from a YouTube video, filtered by chapters if provided.

        Args:
            url: YouTube video URL
            language: Language code for subtitles (default: "en" for English)
            chapters: List of chapters with start_time and title to filter subtitles

        Returns:
            Dict containing success status, subtitle content, and any error information
        """
        try:
            # Create a temporary directory to store the subtitle file
            with tempfile.TemporaryDirectory() as temp_dir:
                output_file = os.path.join(temp_dir, "subtitles")
                
                # Configure yt-dlp options
                ydl_opts = {
                    'skip_download': True,
                    'writesubtitles': True,
                    'writeautomaticsub': True,  # Also try auto-generated subs if regular ones aren't available
                    'subtitleslangs': [language],
                    'subtitlesformat': 'vtt',
                    'outtmpl': output_file,
                    'quiet': True,
                }
                
                # Use yt-dlp library directly
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                
                # Get all chapters for context if we're filtering by chapters
                all_chapters = None
                if chapters and not any(chapter.get('end_time') for chapter in chapters):
                    # Get all chapters from video metadata
                    all_chapters = info.get('chapters', [])
                    
                    # If no chapters in video metadata, create a single chapter for the whole video
                    if not all_chapters and info.get('duration'):
                        all_chapters = [{
                            'start_time': 0,
                            'end_time': info.get('duration', 0),
                            'title': info.get('title', 'Full Video')
                        }]
                    
                    # Sort all chapters by start time
                    all_chapters = sorted(all_chapters, key=lambda x: x.get('start_time', 0))
                
                # Check if the subtitle file was created
                subtitle_file = f"{output_file}.{language}.vtt"
                if os.path.exists(subtitle_file):
                    with open(subtitle_file, 'r', encoding='utf-8') as f:
                        subtitle_content = f.read()
                    
                    # Get video duration if available
                    duration = info.get('duration', 0)
                    
                    # Process the VTT content to make it more readable, filtered by chapters
                    processed_content = self._process_vtt_content(subtitle_content, chapters, all_chapters, duration)
                    
                    return {
                        "success": True,
                        "content": processed_content,
                        "message": "Subtitles successfully extracted" + (" for specified chapters" if chapters else "")
                    }
                else:
                    return {
                        "success": False,
                        "error": f"No subtitles found for language '{language}'"
                    }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to extract subtitles: {str(e)}"
            }
    
    def _process_vtt_content(
        self, 
        vtt_content: str, 
        selected_chapters: Optional[List[Dict[str, Any]]] = None, 
        all_chapters: Optional[List[Dict[str, Any]]] = None,
        video_duration: int = 0
    ) -> str:
        """
        Process VTT subtitle content to make it more readable, filtered by chapters if provided.
        
        Args:
            vtt_content: Raw VTT subtitle content
            selected_chapters: List of specific chapters to extract subtitles for
            all_chapters: Complete list of all chapters in the video (for context)
            video_duration: Total duration of the video in seconds
            
        Returns:
            Processed subtitle text
        """
        lines = vtt_content.split('\n')
        
        # If no chapters provided, process all subtitles
        if not selected_chapters:
            return self._process_all_subtitles(lines)
        
        # Create chapter ranges with start and end times
        chapter_ranges = []
        
        # Sort selected chapters by start time
        selected_chapters = sorted(selected_chapters, key=lambda x: x.get('start_time', 0))
        
        for chapter in selected_chapters:
            start_time = chapter.get('start_time', 0)
            title = chapter.get('title', 'Unnamed chapter')
            
            # If chapter has explicit end_time, use it
            if 'end_time' in chapter:
                end_time = chapter['end_time']
            else:
                # Find this chapter in all_chapters to determine its end time
                end_time = None
                
                if all_chapters:
                    # Find the current chapter in all_chapters
                    for i, full_chapter in enumerate(all_chapters):
                        if (full_chapter.get('start_time') == start_time and 
                            full_chapter.get('title') == title):
                            # If this is the last chapter, end time is video duration
                            if i == len(all_chapters) - 1:
                                end_time = video_duration
                            else:
                                # Otherwise, end time is the start time of the next chapter
                                end_time = all_chapters[i+1].get('start_time')
                            break
                
                # If we couldn't find the end time, use the next chapter's start time or video duration
                if end_time is None:
                    # Find the next chapter in selected_chapters that has a later start time
                    next_chapters = [c for c in selected_chapters if c.get('start_time', 0) > start_time]
                    if next_chapters:
                        end_time = min(c.get('start_time', video_duration) for c in next_chapters)
                    else:
                        end_time = video_duration
            
            chapter_ranges.append({
                'start': start_time,
                'end': end_time,
                'title': title
            })
        
        # Process subtitles by chapter
        result = []
        for chapter_range in chapter_ranges:
            chapter_subs = self._extract_subtitles_for_timerange(
                lines, 
                chapter_range['start'], 
                chapter_range['end']
            )
            if chapter_subs:
                result.append(f"## {chapter_range['title']}")
                result.append(chapter_subs)
        
        return '\n\n'.join(result)

    def _process_all_subtitles(self, lines: list) -> str:
        """Process all subtitles without chapter filtering."""
        processed_lines = []
        
        # Skip header lines
        start_processing = False
        current_text = ""
        
        for line in lines:
            # Skip empty lines and timing information
            if not line.strip():
                continue
            
            # Skip VTT header
            if not start_processing:
                if line.strip() and not line.startswith('WEBVTT'):
                    start_processing = True
                else:
                    continue
            
            # Skip timing lines (they contain --> )
            if '-->' in line:
                continue
                
            # Skip lines with just numbers (timestamp indices)
            if line.strip().isdigit():
                continue
                
            # Add non-empty content lines
            if line.strip():
                if current_text and not current_text.endswith('.'):
                    current_text += " "
                current_text += line.strip()
                
                # If line ends with period, add to processed lines
                if line.strip().endswith('.'):
                    processed_lines.append(current_text)
                    current_text = ""
        
        # Add any remaining text
        if current_text:
            processed_lines.append(current_text)
            
        return '\n'.join(processed_lines)

    def _extract_subtitles_for_timerange(self, lines: list, start_seconds: float, end_seconds: float) -> str:
        """
        Extract subtitles that fall within a specific time range.
        
        Args:
            lines: VTT subtitle lines
            start_seconds: Start time in seconds
            end_seconds: End time in seconds
            
        Returns:
            Processed subtitle text for the time range
        """
        processed_lines = []
        current_text = ""
        current_time = 0
        include_line = False
        
        for i, line in enumerate(lines):
            # Parse timestamp lines
            if '-->' in line:
                time_parts = line.split('-->')
                if len(time_parts) >= 1:
                    # Parse the start time
                    time_str = time_parts[0].strip()
                    try:
                        # Handle different time formats (00:00:00.000 or 00:00.000)
                        if time_str.count(':') == 2:
                            h, m, s = time_str.split(':')
                            current_time = int(h) * 3600 + int(m) * 60 + float(s)
                        else:
                            m, s = time_str.split(':')
                            current_time = int(m) * 60 + float(s)
                        
                        # Check if this subtitle falls within our chapter range
                        include_line = start_seconds <= current_time < end_seconds
                    except (ValueError, IndexError):
                        include_line = False
                continue
            
            # Skip empty lines, header, and timestamp indices
            if not line.strip() or line.startswith('WEBVTT') or line.strip().isdigit():
                continue
                
            # Process content lines if they're in our time range
            if include_line and line.strip():
                if current_text and not current_text.endswith('.'):
                    current_text += " "
                current_text += line.strip()
                
                # If line ends with period, add to processed lines
                if line.strip().endswith('.'):
                    processed_lines.append(current_text)
                    current_text = ""
        
        # Add any remaining text
        if current_text:
            processed_lines.append(current_text)
            
        return '\n'.join(processed_lines)
    
    def _format_time(self, seconds: float) -> str:
        """
        Format time in seconds to HH:MM:SS format.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def extract_chapters(self, url: str) -> Dict[str, Any]:
        """
        Extract chapters from a YouTube video.

        Args:
            url: YouTube video URL

        Returns:
            Dict containing success status, chapters information, and any error information
        """
        try:
            # Configure yt-dlp options
            ydl_opts = {
                'skip_download': True,
                'quiet': True,
            }
            
            # Use yt-dlp library directly
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
            # Get video title
            video_title = info.get('title', 'Untitled Video')
            
            # Check if chapters information is available
            if info and 'chapters' in info and info['chapters']:
                chapters = info['chapters']
                
                # Format chapters information
                formatted_chapters = []
                for chapter in chapters:
                    start_time = self._format_time(chapter.get('start_time', 0))
                    title = chapter.get('title', 'Unnamed chapter')
                    formatted_chapters.append(f"{start_time} - {title}")
                
                chapters_text = "\n".join(formatted_chapters)
                
                return {
                    "success": True,
                    "content": chapters_text,
                    "message": f"Successfully extracted {len(chapters)} chapters",
                    "raw_chapters": chapters  # Include raw data for potential further processing
                }
            else:
                # No chapters found, return video title as a single chapter
                formatted_chapter = f"00:00 - {video_title}"
                
                return {
                    "success": True,
                    "content": formatted_chapter,
                    "message": "No chapters found. Returning video title as a single chapter.",
                    "raw_chapters": [{
                        "start_time": 0,
                        "title": video_title
                    }]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to extract chapters: {str(e)}"
            }
