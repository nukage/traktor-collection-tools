"""HTML preview generator for Traktor Collection Tools."""

import json
from datetime import datetime
from typing import Optional

from missing import MissingFileInfo, MISSING_CATEGORIES
from duplicates import DuplicateGroup, Track


def format_playtime(seconds: float) -> str:
    """Format playtime in mm:ss."""
    if seconds <= 0:
        return "0:00"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    if not text:
        return ""
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;"))


def serialize_track(track: Track) -> dict:
    """Serialize a Track to a JSON-serializable dict."""
    return {
        "title": track.title,
        "artist": track.artist,
        "file_path": track.file_path,
        "volume": track.volume,
        "volume_id": track.volume_id,
        "album": track.album,
        "bpm": track.bpm,
        "bpm_quality": track.bpm_quality,
        "musical_key": track.musical_key,
        "playtime": track.playtime,
        "playcount": track.playcount,
        "import_date": track.import_date,
        "last_played": track.last_played,
        "bitrate": track.bitrate,
        "file_size": track.file_size,
        "peak_db": track.peak_db,
        "perceived_db": track.perceived_db,
        "analyzed_db": track.analyzed_db,
        "audio_id": track.audio_id,
        "cues": [{"name": c.name, "type": c.type, "start": c.start, "length": c.length,
                  "repeats": c.repeats, "hotcue": c.hotcue, "color": c.color} for c in track.cues],
        "stems": track.stems,
        "full_path": track.full_path,
    }


def serialize_missing_info(info: MissingFileInfo) -> dict:
    """Serialize a MissingFileInfo to a JSON-serializable dict."""
    return {
        "track": serialize_track(info.track),
        "original_path": info.original_path,
        "status": info.status,
        "found_paths": info.found_paths,
        "full_path": info.full_path,
    }


def serialize_duplicate_group(group: DuplicateGroup, index: int) -> dict:
    """Serialize a DuplicateGroup to a JSON-serializable dict."""
    return {
        "group_id": index,
        "normalized_key": group.normalized_key,
        "tracks": [serialize_track(t) for t in group.tracks],
        "winner": serialize_track(group.winner) if group.winner else None,
        "same_file": group.same_file,
    }


def generate_preview_html(
    missing: list[MissingFileInfo],
    duplicates: list[DuplicateGroup],
    filters: Optional[dict] = None
) -> str:
    """Generate an interactive HTML preview page."""
    if filters is None:
        filters = {}

    timestamp = datetime.now().isoformat()

    missing_serialized = [serialize_missing_info(m) for m in missing]
    duplicates_serialized = [serialize_duplicate_group(g, i) for i, g in enumerate(duplicates)]

    data_json = json.dumps({
        "missing": missing_serialized,
        "duplicates": duplicates_serialized,
        "generated_at": timestamp,
    }, indent=2)

    timestamp_escaped = escape_html(timestamp)

    html_parts = []
    html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Traktor Collection Preview</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        :root {
            --bg-primary: #0d0d0d;
            --bg-secondary: #1a1a1a;
            --bg-tertiary: #252525;
            --bg-hover: #2a2a2a;
            --text-primary: #e0e0e0;
            --text-secondary: #a0a0a0;
            --accent: #ff6b35;
            --accent-hover: #ff8c5a;
            --success: #4ade80;
            --warning: #fbbf24;
            --danger: #ef4444;
            --border: #333333;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            padding: 16px 24px;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            color: var(--accent);
        }

        .filter-bar {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: center;
        }

        .filter-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .filter-group label {
            font-size: 13px;
            color: var(--text-secondary);
        }

        input[type="text"], select {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 14px;
        }

        input[type="text"]:focus, select:focus {
            outline: none;
            border-color: var(--accent);
        }

        input[type="number"] {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 14px;
            width: 80px;
        }

        input[type="number"]:focus {
            outline: none;
            border-color: var(--accent);
        }

        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
        }

        .checkbox-group input[type="checkbox"] {
            width: 16px;
            height: 16px;
            accent-color: var(--accent);
        }

        .search-input {
            width: 250px;
        }

        main {
            flex: 1;
            padding: 16px 24px;
            overflow-x: auto;
        }

        .table-container {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }

        th {
            background: var(--bg-secondary);
            text-align: left;
            padding: 12px 16px;
            font-weight: 600;
            color: var(--text-secondary);
            border-bottom: 2px solid var(--border);
            white-space: nowrap;
        }

        td {
            padding: 10px 16px;
            border-bottom: 1px solid var(--border);
            vertical-align: middle;
        }

        tr:nth-child(even) {
            background: var(--bg-secondary);
        }

        tr:nth-child(odd) {
            background: var(--bg-primary);
        }

        tr:hover {
            background: var(--bg-hover);
        }

        tr.selected {
            background: rgba(255, 107, 53, 0.15);
        }

        tr.likely-mix {
            border-left: 3px solid var(--warning);
        }

        tr.expandable {
            cursor: pointer;
        }

        tr.expandable .expand-icon {
            display: inline-block;
            width: 16px;
            transition: transform 0.2s;
        }

        tr.expandable.expanded .expand-icon {
            transform: rotate(90deg);
        }

        .type-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }

        .type-icon.missing {
            background: rgba(239, 68, 68, 0.2);
            color: var(--danger);
        }

        .type-icon.duplicate {
            background: rgba(255, 107, 53, 0.2);
            color: var(--accent);
        }

        .playtime {
            font-family: 'Consolas', 'Monaco', monospace;
        }

        .playtime.long {
            color: var(--warning);
            font-weight: 600;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-badge.missing {
            background: rgba(239, 68, 68, 0.2);
            color: var(--danger);
        }

        .status-badge.found_single {
            background: rgba(74, 222, 128, 0.2);
            color: var(--success);
        }

        .status-badge.found_multiple {
            background: rgba(251, 191, 36, 0.2);
            color: var(--warning);
        }

        .status-badge.network_offline {
            background: rgba(160, 160, 160, 0.2);
            color: var(--text-secondary);
        }

        .winner-badge {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            background: var(--accent);
            color: #000;
            font-weight: 700;
            margin-left: 6px;
        }

        .duplicate-expand-row {
            display: none;
        }

        .duplicate-expand-row.visible {
            display: table-row;
        }

        .duplicate-expand-content {
            background: var(--bg-tertiary) !important;
            padding: 12px 16px !important;
        }

        .duplicate-expand-content td {
            padding: 8px 16px;
            border-bottom: 1px solid var(--border);
        }

        .duplicate-sub-table {
            width: 100%;
            border-collapse: collapse;
        }

        .duplicate-sub-table th {
            background: var(--bg-secondary);
            padding: 8px 12px;
            font-size: 12px;
            color: var(--text-secondary);
        }

        .duplicate-sub-table td {
            padding: 6px 12px;
            font-size: 13px;
        }

        .winner-row td {
            background: rgba(255, 107, 53, 0.1);
        }

        .found-path {
            font-size: 12px;
            color: var(--success);
            margin-top: 4px;
            word-break: break-all;
        }

        .selection-bar {
            background: var(--bg-secondary);
            border-top: 1px solid var(--border);
            padding: 12px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }

        .selection-info {
            font-size: 14px;
            color: var(--text-secondary);
        }

        .selection-info strong {
            color: var(--accent);
        }

        .selection-actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        button {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }

        button:hover {
            background: var(--bg-hover);
            border-color: var(--accent);
        }

        button.primary {
            background: var(--accent);
            border-color: var(--accent);
            color: #000;
            font-weight: 600;
        }

        button.primary:hover {
            background: var(--accent-hover);
        }

        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        footer {
            background: var(--bg-secondary);
            border-top: 1px solid var(--border);
            padding: 12px 24px;
            text-align: center;
            font-size: 12px;
            color: var(--text-secondary);
        }

        .empty-state {
            text-align: center;
            padding: 48px 24px;
            color: var(--text-secondary);
        }

        .empty-state h3 {
            margin-bottom: 8px;
            color: var(--text-primary);
        }

        .radioWinner {
            accent-color: var(--accent);
            width: 16px;
            height: 16px;
            cursor: pointer;
        }

        @media (max-width: 768px) {
            .filter-bar {
                flex-direction: column;
                align-items: stretch;
            }

            .filter-group {
                flex-wrap: wrap;
            }

            .search-input {
                width: 100%;
            }

            .selection-bar {
                flex-direction: column;
                align-items: flex-start;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="header-title">Traktor Collection Preview</div>
        <div class="filter-bar">
            <div class="filter-group">
                <input type="text" id="searchInput" class="search-input" placeholder="Search artist or title...">
            </div>
            <div class="filter-group">
                <label for="categoryFilter">Category:</label>
                <select id="categoryFilter">
                    <option value="all">All</option>
                    <option value="missing">Missing</option>
                    <option value="found_single">Found (Single)</option>
                    <option value="found_multiple">Found (Multiple)</option>
                    <option value="network_offline">Network Offline</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Playtime:</label>
                <input type="number" id="minPlaytime" placeholder="min (s)" min="0">
                <span>-</span>
                <input type="number" id="maxPlaytime" placeholder="max (s)" min="0">
            </div>
            <div class="filter-group">
                <label class="checkbox-group">
                    <input type="checkbox" id="showMissing" checked>
                    <span>Show Missing</span>
                </label>
            </div>
            <div class="filter-group">
                <label class="checkbox-group">
                    <input type="checkbox" id="showDuplicates" checked>
                    <span>Show Duplicates</span>
                </label>
            </div>
            <button id="selectAllVisible">Select All Visible</button>
        </div>
    </header>

    <main>
        <div class="table-container">
            <table id="trackTable">
                <thead>
                    <tr>
                        <th><input type="checkbox" id="selectAllCheckbox"></th>
                        <th></th>
                        <th>Artist</th>
                        <th>Title</th>
                        <th>BPM</th>
                        <th>Playtime</th>
                        <th>Status / Info</th>
                    </tr>
                </thead>
                <tbody id="trackList">
                </tbody>
            </table>
            <div id="emptyState" class="empty-state" style="display: none;">
                <h3>No items to display</h3>
                <p>Try adjusting your filters.</p>
            </div>
        </div>
    </main>

    <div class="selection-bar">
        <div class="selection-info">
            <span id="selectionCount">0</span> items selected
        </div>
        <div class="selection-actions">
            <button id="acceptAllFound" disabled>Accept All Found</button>
            <button id="ignoreAll" disabled>Ignore All</button>
            <button id="exportSelection" disabled>Export Selection</button>
        </div>
    </div>

    <footer>
        Generated: <span id="generatedAt">__TIMESTAMP__</span>
    </footer>

    <script>
    const APP_DATA = __DATA_JSON__;

    const state = {
        selectedIds: new Set(),
        lastClickedIndex: -1,
        filters: {
            search: '',
            category: 'all',
            minPlaytime: null,
            maxPlaytime: null,
            showMissing: true,
            showDuplicates: true,
        },
    };

    const STORAGE_KEY = 'traktor-preview-selection';

    function loadSelection() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
                const data = JSON.parse(saved);
                if (data.selectedIds) {
                    state.selectedIds = new Set(data.selectedIds);
                }
            }
        } catch (e) {
            console.warn('Failed to load selection from localStorage', e);
        }
    }

    function saveSelection() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify({
                selectedIds: Array.from(state.selectedIds)
            }));
        } catch (e) {
            console.warn('Failed to save selection to localStorage', e);
        }
    }

    function getItemId(item, type) {
        if (type === 'missing') {
            return 'missing_' + item.track.audio_id;
        } else if (type === 'duplicate') {
            return 'dup_' + item.group_id;
        }
        return '';
    }

    function getAllVisibleItems() {
        const items = [];
        const {missing, duplicates} = APP_DATA;

        if (state.filters.showMissing) {
            for (const m of missing) {
                if (matchesFilters(m, 'missing')) {
                    items.push({ item: m, type: 'missing' });
                }
            }
        }

        if (state.filters.showDuplicates) {
            for (const d of duplicates) {
                if (matchesFilters(d, 'duplicate')) {
                    items.push({ item: d, type: 'duplicate' });
                }
            }
        }

        return items;
    }

    function matchesFilters(item, type) {
        const {search, category, minPlaytime, maxPlaytime} = state.filters;

        if (search) {
            const searchLower = search.toLowerCase();
            let text = '';
            if (type === 'missing') {
                text = (item.track.artist + ' ' + item.track.title).toLowerCase();
            } else {
                text = (item.normalized_key || '').toLowerCase();
            }
            if (!text.includes(searchLower)) {
                return false;
            }
        }

        if (type === 'missing') {
            if (category !== 'all' && item.status !== category) {
                return false;
            }
            const pt = item.track.playtime || 0;
            if (minPlaytime !== null && pt < minPlaytime) return false;
            if (maxPlaytime !== null && pt > maxPlaytime) return false;
        } else if (type === 'duplicate') {
            const pt = item.winner ? (item.winner.playtime || 0) : 0;
            if (minPlaytime !== null && pt < minPlaytime) return false;
            if (maxPlaytime !== null && pt > maxPlaytime) return false;
        }

        return true;
    }

    function isLongTrack(playtime) {
        return playtime && playtime > 600;
    }

    function formatPlaytime(seconds) {
        if (!seconds || seconds <= 0) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return mins + ':' + (secs < 10 ? '0' : '') + secs;
    }

    function escapeHtml(text) {
        if (text === null || text === undefined) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function truncatePath(path, maxLen) {
        if (!path) return '';
        maxLen = maxLen || 40;
        if (path.length <= maxLen) return escapeHtml(path);
        return '...' + escapeHtml(path.slice(-maxLen));
    }

    function renderMissingRow(m) {
        const id = 'missing_' + m.track.audio_id;
        const isSelected = state.selectedIds.has(id);
        const isLong = isLongTrack(m.track.playtime);
        let rowClass = 'expandable';
        if (isSelected) rowClass += ' selected';
        if (isLong) rowClass += ' likely-mix';

        let statusBadge = '';
        if (m.status === 'missing') {
            statusBadge = '<span class="status-badge missing">MISSING</span>';
        } else if (m.status === 'found_single') {
            statusBadge = '<span class="status-badge found_single">FOUND</span>';
        } else if (m.status === 'found_multiple') {
            statusBadge = '<span class="status-badge found_multiple">MULTIPLE</span>';
        } else if (m.status === 'network_offline') {
            statusBadge = '<span class="status-badge network_offline">OFFLINE</span>';
        }

        let foundPath = '';
        if (m.found_paths && m.found_paths.length > 0) {
            foundPath = '<div class="found-path">Found: ' + escapeHtml(m.found_paths[0]) + '</div>';
        }

        return '<tr class="' + rowClass + '" data-id="' + id + '" data-type="missing" data-index="' + m._index + '">' +
            '<td><input type="checkbox" class="row-checkbox"' + (isSelected ? ' checked' : '') + '></td>' +
            '<td><span class="type-icon missing">!</span></td>' +
            '<td>' + escapeHtml(m.track.artist) + '</td>' +
            '<td>' + escapeHtml(m.track.title) + '</td>' +
            '<td>' + (m.track.bpm ? m.track.bpm.toFixed(1) : '-') + '</td>' +
            '<td><span class="playtime' + (isLong ? ' long' : '') + '">' + formatPlaytime(m.track.playtime) + '</span></td>' +
            '<td>' + statusBadge + foundPath + '</td>' +
            '</tr>';
    }

    function renderDuplicateRow(d, index) {
        const id = 'dup_' + d.group_id;
        const isSelected = state.selectedIds.has(id);
        const isLong = isLongTrack(d.winner ? d.winner.playtime : 0);
        let rowClass = 'expandable';
        if (isSelected) rowClass += ' selected';
        if (isLong) rowClass += ' likely-mix';

        let statusInfo = d.same_file ? 'Same file' : 'Different files';
        if (d.tracks && d.tracks.length > 2) {
            statusInfo += ' (+' + (d.tracks.length - 2) + ' more)';
        }

        const winnerBadge = (d.winner ? '<span class="winner-badge">WINNER</span>' : '');
        return '<tr class="' + rowClass + '" data-id="' + id + '" data-type="duplicate" data-group="' + d.group_id + '" data-index="' + index + '">' +
            '<td><input type="checkbox" class="row-checkbox"' + (isSelected ? ' checked' : '') + '></td>' +
            '<td><span class="type-icon duplicate">D</span></td>' +
            '<td>' + escapeHtml(d.winner ? d.winner.artist : '-') + '</td>' +
            '<td>' + escapeHtml(d.winner ? d.winner.title : '-') + winnerBadge + '</td>' +
            '<td>' + (d.winner && d.winner.bpm ? d.winner.bpm.toFixed(1) : '-') + '</td>' +
            '<td><span class="playtime' + (isLong ? ' long' : '') + '">' + formatPlaytime(d.winner ? d.winner.playtime : 0) + '</span></td>' +
            '<td><span style="color: var(--text-secondary);">' + statusInfo + '</span></td>' +
            '</tr>';
    }

    function renderDuplicateExpandRow(d) {
        let tracksHtml = '';
        const winnerId = d.winner ? d.winner.audio_id : '';

        for (const track of d.tracks) {
            const isWinner = track.audio_id === winnerId;
            const isRowLong = isLongTrack(track.playtime);
            tracksHtml += '<tr class="' + (isWinner ? 'winner-row' : '') + '">' +
                '<td><input type="radio" name="winner_' + d.group_id + '" class="radioWinner" value="' + track.audio_id + '"' + (isWinner ? ' checked' : '') + ' data-group="' + d.group_id + '"></td>' +
                '<td>' + escapeHtml(track.artist) + '</td>' +
                '<td>' + escapeHtml(track.title) + '</td>' +
                '<td>' + (track.bpm ? track.bpm.toFixed(1) : '-') + '</td>' +
                '<td><span class="playtime' + (isRowLong ? ' long' : '') + '">' + formatPlaytime(track.playtime) + '</span></td>' +
                '<td>' + (track.file_size / 1000000).toFixed(1) + ' MB</td>' +
                '<td>' + (isWinner ? '<span class="winner-badge">WINNER</span>' : '') + '</td>' +
                '</tr>';
        }

        return '<tr class="duplicate-expand-row" data-group="' + d.group_id + '">' +
            '<td colspan="7" class="duplicate-expand-content">' +
            '<table class="duplicate-sub-table">' +
            '<thead><tr><th></th><th>Artist</th><th>Title</th><th>BPM</th><th>Playtime</th><th>Size</th><th></th></tr></thead>' +
            '<tbody>' + tracksHtml + '</tbody>' +
            '</table></td></tr>';
    }

    function render() {
        const tbody = document.getElementById('trackList');
        const emptyState = document.getElementById('emptyState');
        const tableContainer = document.querySelector('.table-container');

        let html = '';
        const {missing, duplicates} = APP_DATA;
        let index = 0;

        if (state.filters.showMissing) {
            for (const m of missing) {
                m._index = index;
                if (matchesFilters(m, 'missing')) {
                    html += renderMissingRow(m);
                    index++;
                }
            }
        }

        if (state.filters.showDuplicates) {
            for (const d of duplicates) {
                d._index = index;
                if (matchesFilters(d, 'duplicate')) {
                    html += renderDuplicateRow(d, index);
                    html += renderDuplicateExpandRow(d);
                    index++;
                }
            }
        }

        if (html) {
            tbody.innerHTML = html;
            emptyState.style.display = 'none';
            tableContainer.style.display = 'block';
            bindRowEvents();
        } else {
            tbody.innerHTML = '';
            emptyState.style.display = 'block';
            tableContainer.style.display = 'none';
        }

        updateSelectionUI();
        updateExpandStates();
    }

    function bindRowEvents() {
        const rows = document.querySelectorAll('#trackList tr[data-id]');

        rows.forEach(row => {
            row.addEventListener('click', handleRowClick);
        });

        const checkboxes = document.querySelectorAll('.row-checkbox');
        checkboxes.forEach(cb => {
            cb.addEventListener('click', handleCheckboxClick);
        });

        const radioBtns = document.querySelectorAll('.radioWinner');
        radioBtns.forEach(radio => {
            radio.addEventListener('change', handleWinnerChange);
        });
    }

    function handleRowClick(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'RADIO') {
            return;
        }

        const row = e.currentTarget;
        const id = row.dataset.id;
        const type = row.dataset.type;
        const index = parseInt(row.dataset.index);

        if (e.shiftKey && state.lastClickedIndex >= 0) {
            const visibleRows = Array.from(document.querySelectorAll('#trackList tr[data-id]'));
            const startIdx = Math.min(state.lastClickedIndex, index);
            const endIdx = Math.max(state.lastClickedIndex, index);

            visibleRows.forEach((r, i) => {
                if (i >= startIdx && i <= endIdx) {
                    state.selectedIds.add(r.dataset.id);
                }
            });
        } else if (e.ctrlKey || e.metaKey) {
            if (state.selectedIds.has(id)) {
                state.selectedIds.delete(id);
            } else {
                state.selectedIds.add(id);
            }
        } else {
            if (state.selectedIds.has(id) && state.selectedIds.size === 1) {
                state.selectedIds.clear();
            } else {
                state.selectedIds.clear();
                state.selectedIds.add(id);
            }
        }

        state.lastClickedIndex = index;
        saveSelection();
        render();

        if (type === 'duplicate') {
            toggleExpand(row.dataset.group, true);
        }
    }

    function handleCheckboxClick(e) {
        e.stopPropagation();
        const row = e.target.closest('tr');
        const id = row.dataset.id;

        if (e.target.checked) {
            state.selectedIds.add(id);
        } else {
            state.selectedIds.delete(id);
        }

        saveSelection();
        updateSelectionUI();
    }

    function handleWinnerChange(e) {
        const audioId = e.target.value;
        const groupId = e.target.dataset.group;

        const group = APP_DATA.duplicates.find(d => d.group_id === parseInt(groupId));
        if (group) {
            const track = group.tracks.find(t => t.audio_id === audioId);
            if (track) {
                group.winner = track;
            }
        }
    }

    function toggleExpand(groupId, forceOpen) {
        if (forceOpen === undefined) forceOpen = false;

        const expandRow = document.querySelector('.duplicate-expand-row[data-group="' + groupId + '"]');
        const headerRow = document.querySelector('tr[data-group="' + groupId + '"]');

        if (!expandRow || !headerRow) return;

        const isExpanded = expandRow.classList.contains('visible');

        if (forceOpen && !isExpanded) {
            expandRow.classList.add('visible');
            headerRow.classList.add('expanded');
        } else if (!forceOpen) {
            expandRow.classList.toggle('visible');
            headerRow.classList.toggle('expanded');
        }
    }

    function updateExpandStates() {
        document.querySelectorAll('.duplicate-expand-row').forEach(row => {
            const groupId = row.dataset.group;
            const headerRow = document.querySelector('tr[data-group="' + groupId + '"]');
            if (headerRow && !row.classList.contains('visible')) {
                headerRow.classList.remove('expanded');
            }
        });
    }

    function updateSelectionUI() {
        document.getElementById('selectionCount').textContent = state.selectedIds.size;

        const hasSelection = state.selectedIds.size > 0;
        const hasFound = Array.from(state.selectedIds).some(id => {
            if (id.startsWith('missing_')) {
                const m = APP_DATA.missing.find(x => 'missing_' + x.track.audio_id === id);
                return m && (m.status === 'found_single' || m.status === 'found_multiple');
            }
            return false;
        });

        document.getElementById('acceptAllFound').disabled = !hasFound;
        document.getElementById('ignoreAll').disabled = !hasSelection;
        document.getElementById('exportSelection').disabled = !hasSelection;

        document.getElementById('selectAllCheckbox').checked = false;
        const visibleRows = document.querySelectorAll('#trackList tr[data-id]');
        if (visibleRows.length > 0 && state.selectedIds.size === visibleRows.length) {
            document.getElementById('selectAllCheckbox').checked = true;
        }
    }

    function selectAllVisible() {
        const visibleRows = document.querySelectorAll('#trackList tr[data-id]');
        visibleRows.forEach(row => {
            state.selectedIds.add(row.dataset.id);
        });
        saveSelection();
        render();
    }

    function acceptAllFound() {
        for (const id of state.selectedIds) {
            if (id.startsWith('missing_')) {
                const m = APP_DATA.missing.find(x => 'missing_' + x.track.audio_id === id);
                if (m && (m.status === 'found_single' || m.status === 'found_multiple')) {
                    m._action = 'rebase';
                    m._selected_path = m.found_paths && m.found_paths[0] ? m.found_paths[0] : null;
                }
            }
        }
        render();
    }

    function ignoreAll() {
        for (const id of state.selectedIds) {
            if (id.startsWith('missing_')) {
                const m = APP_DATA.missing.find(x => 'missing_' + x.track.audio_id === id);
                if (m) {
                    m._action = 'ignore';
                }
            } else if (id.startsWith('dup_')) {
                const d = APP_DATA.duplicates.find(x => 'dup_' + x.group_id === id);
                if (d) {
                    d._action = 'ignore';
                }
            }
        }
        render();
    }

    function exportSelection() {
        const result = {
            created: new Date().toISOString(),
            missing: [],
            duplicates: [],
            excluded: []
        };

        for (const id of state.selectedIds) {
            if (id.startsWith('missing_')) {
                const m = APP_DATA.missing.find(x => 'missing_' + x.track.audio_id === id);
                if (m) {
                    const entry = {
                        audio_id: m.track.audio_id
                    };

                    if (m._action === 'rebase') {
                        entry.action = 'rebase';
                        if (m._selected_path) {
                            entry.new_path = m._selected_path;
                        } else if (m.found_paths && m.found_paths[0]) {
                            entry.new_path = m.found_paths[0];
                        }
                    } else if (m._action === 'ignore') {
                        entry.action = 'ignore';
                    } else if (m.status === 'found_single' || m.status === 'found_multiple') {
                        entry.action = 'rebase';
                        entry.new_path = m.found_paths && m.found_paths[0] ? m.found_paths[0] : undefined;
                    } else {
                        entry.action = 'ignore';
                    }

                    result.missing.push(entry);
                }
            } else if (id.startsWith('dup_')) {
                const d = APP_DATA.duplicates.find(x => 'dup_' + x.group_id === id);
                if (d) {
                    const entry = {
                        group_id: d.group_id
                    };

                    if (d._action === 'ignore') {
                        entry.action = 'ignore';
                    } else {
                        entry.action = 'merge';
                        entry.winner_id = d.winner ? d.winner.audio_id : undefined;
                    }

                    result.duplicates.push(entry);
                }
            }
        }

        const json = JSON.stringify(result, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'traktor-selection-' + new Date().toISOString().slice(0, 10) + '.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function bindFilterEvents() {
        const searchInput = document.getElementById('searchInput');
        const categoryFilter = document.getElementById('categoryFilter');
        const minPlaytime = document.getElementById('minPlaytime');
        const maxPlaytime = document.getElementById('maxPlaytime');
        const showMissing = document.getElementById('showMissing');
        const showDuplicates = document.getElementById('showDuplicates');

        searchInput.addEventListener('input', () => {
            state.filters.search = searchInput.value;
            render();
        });

        categoryFilter.addEventListener('change', () => {
            state.filters.category = categoryFilter.value;
            render();
        });

        minPlaytime.addEventListener('input', () => {
            state.filters.minPlaytime = minPlaytime.value ? parseInt(minPlaytime.value) : null;
            render();
        });

        maxPlaytime.addEventListener('input', () => {
            state.filters.maxPlaytime = maxPlaytime.value ? parseInt(maxPlaytime.value) : null;
            render();
        });

        showMissing.addEventListener('change', () => {
            state.filters.showMissing = showMissing.checked;
            render();
        });

        showDuplicates.addEventListener('change', () => {
            state.filters.showDuplicates = showDuplicates.checked;
            render();
        });

        document.getElementById('selectAllVisible').addEventListener('click', selectAllVisible);
        document.getElementById('selectAllCheckbox').addEventListener('change', (e) => {
            if (e.target.checked) {
                selectAllVisible();
            } else {
                state.selectedIds.clear();
                saveSelection();
                render();
            }
        });

        document.getElementById('acceptAllFound').addEventListener('click', acceptAllFound);
        document.getElementById('ignoreAll').addEventListener('click', ignoreAll);
        document.getElementById('exportSelection').addEventListener('click', exportSelection);
    }

    document.addEventListener('DOMContentLoaded', () => {
        loadSelection();
        bindFilterEvents();
        render();
    });
    </script>
</body>
</html>""")

    html = "".join(html_parts)
    html = html.replace("__DATA_JSON__", data_json)
    html = html.replace("__TIMESTAMP__", timestamp_escaped)
    return html


if __name__ == "__main__":
    import sys
    sys.path.insert(0, 'src')

    from parser import Track, Cue
    from missing import MissingFileInfo
    from duplicates import DuplicateGroup

    tracks = [
        Track(
            title="Test Track 1",
            artist="Artist One",
            file_path="Music/Track1.mp3",
            volume="E:",
            volume_id="vol1",
            bpm=128.5,
            playtime=180.0,
            bitrate=320000,
            file_size=8000000,
            audio_id="abc123",
        ),
        Track(
            title="Test Track 2",
            artist="Artist Two",
            file_path="Music/Track2.mp3",
            volume="E:",
            volume_id="vol1",
            bpm=130.0,
            playtime=360.0,
            bitrate=256000,
            file_size=12000000,
            audio_id="def456",
            cues=[Cue(name="Intro", type=0, start=0.0, length=30.0, repeats=-1, hotcue=1)]
        ),
        Track(
            title="Very Long Mix Track",
            artist="DJ Long",
            file_path="Music/LongMix.mp3",
            volume="E:",
            volume_id="vol1",
            bpm=125.0,
            playtime=4200.0,
            bitrate=320000,
            file_size=150000000,
            audio_id="ghi789",
        ),
        Track(
            title="Duplicate Track",
            artist="Same Artist",
            file_path="Music/Dup1.mp3",
            volume="E:",
            volume_id="vol1",
            bpm=128.0,
            playtime=200.0,
            bitrate=320000,
            file_size=9000000,
            audio_id="dup1a",
        ),
        Track(
            title="Duplicate Track",
            artist="Same Artist",
            file_path="Music/Dup2.mp3",
            volume="E:",
            volume_id="vol1",
            bpm=128.0,
            playtime=200.5,
            bitrate=320000,
            file_size=9500000,
            audio_id="dup1b",
        ),
    ]

    missing = [
        MissingFileInfo(
            track=tracks[0],
            original_path="E:/Music/Track1.mp3",
            status="missing",
            found_paths=[]
        ),
        MissingFileInfo(
            track=tracks[1],
            original_path="E:/Music/Track2.mp3",
            status="found_single",
            found_paths=["E:/NewLocation/Track2.mp3"]
        ),
        MissingFileInfo(
            track=tracks[2],
            original_path="\\\\server/Music/LongMix.mp3",
            status="network_offline",
            found_paths=[]
        ),
    ]

    duplicate_groups = [
        DuplicateGroup(
            normalized_key="same artist | duplicate track",
            tracks=[tracks[3], tracks[4]],
            winner=tracks[3],
            same_file=False,
            merge_actions=[]
        ),
    ]

    print("Generating HTML preview...")
    html = generate_preview_html(missing, duplicate_groups)

    output_path = "preview_test.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated {len(html)} bytes to {output_path}")