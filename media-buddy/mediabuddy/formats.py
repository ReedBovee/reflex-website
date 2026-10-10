"""File-extension catalog for Media Buddy.

Every extension is lowercase with no leading dot. The goal is to catch
anything a camera, scanner, capture card, NLE export, or phone can write as a
video or still-image file -- including the cinema-camera and film-scan
formats a restoration lab actually receives -- while leaving out project
files, playlists, and sidecars that would just clutter an inventory.
"""

VIDEO = {
    # Everyday containers
    "mp4", "m4v", "mov", "qt", "avi", "wmv", "asf", "mkv", "mk3d", "webm",
    "flv", "f4v", "f4p", "ogv", "ogm", "3gp", "3g2", "3gpp", "3gpp2",
    "divx", "xvid", "rm", "rmvb", "amv", "nsv", "gifv", "swf",
    # MPEG program / transport streams, DVD, Blu-ray, AVCHD
    "mpg", "mpeg", "mpe", "mpv", "m1v", "m2v", "mp2v", "m2p", "m4p", "vob",
    "vro", "ts", "tsv", "m2t", "m2ts", "mts", "trp", "tp", "evo", "ssif",
    "mod", "tod", "moi",
    # Raw elementary streams
    "h264", "264", "h265", "265", "hevc", "avc", "vc1", "ivf", "y4m", "yuv",
    # DV / tape capture / broadcast
    "dv", "dif", "mxf", "gxf", "lxf", "mj2", "mjp2", "mjpg", "mjpeg",
    "wtv", "dvr-ms", "tivo", "rec", "nuv", "pva",
    # Cinema and pro cameras
    "r3d", "braw", "ari", "arx", "crm", "cine", "xavc", "mxr", "nev",
    # 360 / action cameras
    "insv", "lrv", "360",
    # Game / animation / legacy
    "bik", "bk2", "smk", "roq", "fli", "flc", "flic", "viv", "vivo", "drc",
    "dav", "k3g", "skm", "dmsm", "dpg", "ismv", "usm",
    # Interchange carrying embedded media
    "aaf", "omf", "omfi",
}

STILL_IMAGE = {
    # JPEG family
    "jpg", "jpeg", "jpe", "jfif", "jfi", "jif", "pjpeg", "pjp", "jp2", "j2k",
    "j2c", "jpc", "jpf", "jpx", "jpm", "jxl", "jxr", "hdp", "wdp", "jls",
    "mpo", "jps",
    # Lossless / web / phone
    "png", "apng", "mng", "jng", "gif", "bmp", "dib", "rle", "tif", "tiff",
    "btf", "tf8", "webp", "heic", "heif", "heics", "heifs", "hif", "avif",
    "avifs", "qoi", "flif", "bpg", "ico", "cur", "icns", "wbmp",
    # Film scan / VFX / HDR
    "dpx", "cin", "exr", "hdr", "rgbe", "pfm", "sgi", "rgb", "rgba", "bw",
    "tga", "targa", "icb", "vda", "vst", "iff", "ilbm", "lbm",
    # Editing / design documents that are fundamentally images
    "psd", "psb", "pdd", "xcf", "kra", "ora", "pdn", "afphoto", "cpt",
    "svg", "svgz", "eps", "epsf", "epsi", "ai", "wmf", "emf", "emz",
    "pict", "pct", "pic", "pcx", "dcx",
    # Photo CD / FlashPix / scanner / archival
    "pcd", "fpx", "djvu", "djv", "jbig", "jbg", "jb2", "jbig2", "fits",
    "fit", "fts", "dcm", "dicom", "pbm", "pgm", "ppm", "pnm", "pam",
    "xbm", "xpm", "xwd", "ras", "sun", "pcf", "pspimage", "psp", "miff",
    "dds", "ktx", "ktx2", "pvr", "wpg", "cals", "sid", "ecw",
}

# Camera and scanner RAW -- still images, reported as their own type.
RAW = {
    "3fr", "arw", "srf", "sr2", "bay", "cap", "cr2", "cr3", "crw", "cs1",
    "dcr", "dcs", "dng", "drf", "eip", "erf", "fff", "gpr", "iiq", "k25",
    "kdc", "mdc", "mef", "mos", "mrw", "nef", "nrw", "obm", "orf", "ori",
    "pef", "ptx", "pxn", "raf", "raw", "rw2", "rwl", "rwz", "srw", "x3f",
    "cri", "lfr", "lfp", "sraw", "mfw", "j6i", "dc2", "kc2", "rdc", "st4",
    "st5", "st6", "st7", "st8", "ia", "bmq", "nksc", "rwr",
}

# Formats a film scanner writes one file per frame. A run of these in one
# folder (reel1_000001.dpx ... reel1_086400.dpx) can collapse to one row.
SEQUENCE_CANDIDATES = {
    "dpx", "cin", "exr", "tif", "tiff", "png", "jpg", "jpeg", "jp2", "j2c",
    "tga", "dng", "bmp", "sgi", "rgb", "psd", "hdr", "cr2", "cr3", "nef",
    "arw", "raw", "webp", "avif", "heic", "jxl", "qoi",
}

# Opt-in: the lab also digitizes audiotape.
AUDIO = {
    "wav", "wave", "bwf", "rf64", "w64", "aif", "aiff", "aifc", "caf",
    "flac", "alac", "ape", "wv", "tta", "tak", "ofr", "shn", "mp3", "mp2",
    "mp1", "mpa", "m4a", "m4b", "m4r", "aac", "adts", "ogg", "oga", "opus",
    "spx", "wma", "ra", "ram", "ac3", "eac3", "ec3", "dts", "dtshd", "mka",
    "mpc", "amr", "awb", "3ga", "au", "snd", "voc", "sd2", "dsf", "dff",
    "mid", "midi", "gsm", "vox", "dss", "ds2", "msv", "dvf", "mlp", "thd",
    "pcm", "8svx", "16svx", "qcp", "act", "aa", "aax", "oma",
}

VIDEO_LABEL = "Video"
IMAGE_LABEL = "Image"
RAW_LABEL = "RAW Image"
AUDIO_LABEL = "Audio"


def classify(ext, include_video=True, include_images=True, include_audio=False):
    """Return the category label for an extension, or None to skip the file."""
    ext = ext.lower().lstrip(".")
    if include_video and ext in VIDEO:
        return VIDEO_LABEL
    if include_images:
        if ext in RAW:
            return RAW_LABEL
        if ext in STILL_IMAGE:
            return IMAGE_LABEL
    if include_audio and ext in AUDIO:
        return AUDIO_LABEL
    return None
