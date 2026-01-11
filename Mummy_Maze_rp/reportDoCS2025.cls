\LoadClassWithOptions{report}
\ProvidesClass{reportDoCS2025}[2025/07/04 Enhanced Report Class for DoCS]

%--------------------------------------
% Class Options
%--------------------------------------
\newif\if@english
\newif\if@vietnamese
\newif\if@final
\newif\if@draft

\DeclareOption{english}{\@englishtrue\@vietnamesefalse}
\DeclareOption{vietnamese}{\@vietnamesetrue\@englishfalse}
\DeclareOption{final}{\@finaltrue\@draftfalse}
\DeclareOption{draft}{\@drafttrue\@finalfalse}

% Default options
\ExecuteOptions{vietnamese,final}
\ProcessOptions\relax

%--------------------------------------
% Required packages (organized by category)
%--------------------------------------

% Language and encoding
\RequirePackage[utf8]{inputenc}
\if@vietnamese
    \RequirePackage[utf8]{vietnam}
\fi
\if@english
    \RequirePackage[english]{babel}
\fi

% Essential packages
\RequirePackage{silence}
\RequirePackage{xcolor}
\RequirePackage{geometry}
\RequirePackage{microtype}
\RequirePackage[fontsize=12pt]{scrextend}

% Text formatting
\RequirePackage{ragged2e}
\RequirePackage{enumitem}
\RequirePackage{titlesec}
\RequirePackage{fancyhdr}
\RequirePackage{url}

% Math packages
\RequirePackage{amsmath,amsfonts,mathtools,amsthm,amssymb,mathrsfs,bm}
\RequirePackage{siunitx}

% Tables and figures
\RequirePackage{booktabs}
\RequirePackage{longtable}
\RequirePackage{tabularx}
\RequirePackage{float}
\RequirePackage{graphicx}
\RequirePackage[justification=centering]{caption}
\RequirePackage{subcaption}

% Graphics and plotting
\RequirePackage{tikz}
\RequirePackage{pgfplots}
\RequirePackage{tcolorbox}

% Code highlighting
\RequirePackage{listings}
\RequirePackage{minted}

% Bibliography and citations
\RequirePackage[
    backend=biber,
    style=ieee,
    sorting=none
]{biblatex}
\RequirePackage{csquotes}

\lstset{
    language=Python,
    backgroundcolor=\color{black},  % Màu nền đen
    basicstyle=\ttfamily\small\color{white},  % Font và cỡ chữ
    keywordstyle=\color{orange},    % Màu từ khóa
    stringstyle=\color{green},      % Màu chuỗi
    commentstyle=\color{gray},      % Màu chú thích
    numberstyle=\tiny\color{gray},  % Màu số dòng
    numbers=left,                  % Hiển thị số dòng
    numbersep=5pt,                 % Khoảng cách số dòng
    frame=single,                  % Khung quanh đoạn code
    breaklines=true,               % Ngắt dòng dài
    showstringspaces=false,        % Không hiển thị khoảng trắng trong chuỗi
    captionpos=b                   % Đặt caption ở dưới
}
% Hyperlinks (load last)
\RequirePackage[hidelinks,colorlinks=true,allcolors=blue]{hyperref}

%--------------------------------------
% Silence warnings
%--------------------------------------
\WarningFilter{fancyhdr}{\headheight is too small}
\WarningFilter{fancyhdr}{\footskip is too small}
\WarningFilter{biblatex}{Patching footnotes failed}

%--------------------------------------
% Enhanced color definitions
%--------------------------------------
\definecolor{centrale_red}{RGB}{178,33,51}
\definecolor{central_blue}{RGB}{31,128,206}
\definecolor{docs_gray}{RGB}{128,128,128}
\definecolor{docs_lightgray}{RGB}{245,245,245}
\definecolor{docs_darkblue}{RGB}{25,102,165}
\definecolor{success_green}{RGB}{40,167,69}
\definecolor{warning_orange}{RGB}{255,193,7}
\definecolor{danger_red}{RGB}{220,53,69}

%--------------------------------------
% Page layout and formatting
%--------------------------------------
\geometry{
    top=2.5cm, 
    bottom=3.0cm, 
    left=2.5cm, 
    right=2.0cm,
    headheight=3cm,
    headsep=1cm,
    footskip=1.5cm
}

\parskip 3pt
\linespread{1.45}
\pgfplotsset{compat=1.18}

% Improved title formatting
\titleformat{\chapter}[display]
    {\bfseries\Large\centering}
    {\if@vietnamese CHƯƠNG \thechapter\else CHAPTER \thechapter\fi}
    {0.5em}
    {\textcolor{central_blue}}
    [\vspace{0.5em}]

\titleformat{\section}
    {\bfseries\large\color{central_blue}}
    {\thesection.}
    {0.5em}
    {}

\titleformat{\subsection}
    {\bfseries\normalsize\color{docs_darkblue}}
    {\thesubsection.}
    {0.5em}
    {}

\titleformat{\subsubsection}
    {\itshape\bfseries\normalsize}
    {\thesubsubsection.}
    {0.5em}
    {}

\titlespacing{\chapter}{0em}{0em}{2em}
\titlespacing{\section}{0em}{1em}{0.5em}
\titlespacing{\subsection}{0em}{0.8em}{0.3em}
\titlespacing{\subsubsection}{0em}{0.5em}{0.2em}

% Enhanced formatting settings
\sisetup{
    output-decimal-marker = {,},
    group-separator = {.},
    group-minimum-digits = 4
}

\renewcommand{\headrulewidth}{0.5pt}
\setlist[itemize]{label=\textbullet, leftmargin=*}
\setlist[itemize,2]{label=\textbf{--}}
\setlist[enumerate]{leftmargin=*, listparindent=1em, parsep=0pt}

%--------------------------------------
% Enhanced metadata commands
%--------------------------------------
\newcommand{\university}[1]{\def\@university{#1}}
\newcommand{\school}[1]{\def\@school{#1}}
\newcommand{\students}[1]{\def\@students{#1}}
\newcommand{\supervisors}[1]{\def\@supervisors{#1}}
\newcommand{\subtitle}[1]{\def\@subtitle{#1}}
\newcommand{\coursecode}[1]{\def\@coursecode{#1}}
\newcommand{\semester}[1]{\def\@semester{#1}}
\newcommand{\academicyear}[1]{\def\@academicyear{#1}}

% Default values
\university{VIETNAM NATIONAL UNIVERSITY, HO CHI MINH CITY}
\school{UNIVERSITY OF SCIENCE\\FACULTY OF INFORMATION TECHNOLOGY}
\subtitle{}
\coursecode{}
\semester{}
\academicyear{}

%--------------------------------------
% Enhanced pagination commands
%--------------------------------------
\newcommand\numRoman{
    \clearpage
    \pagenumbering{roman}
    \setcounter{page}{1}
}

\newcommand\pageNumber{
    \clearpage
    \pagenumbering{arabic}
    \setcounter{page}{1}
}

%--------------------------------------
% Enhanced header and footer
%--------------------------------------
\pagestyle{fancy}
\fancyhf{}

% Main page style
% \fancyhead[L]{\footnotesize\textcolor{docs_gray}{\@title}}
% \fancyhead[R]{\footnotesize\textcolor{docs_gray}{\@university}}
% \fancyfoot[C]{\textbf{\thepage}}
\renewcommand{\headrulewidth}{0.5pt}
\renewcommand{\footrulewidth}{0pt}


%--------------------------------------
% Enhanced cover page
%--------------------------------------
\newcommand{\cover}{
    \begin{titlepage}
        \begin{center}
            \vspace*{1cm}
            
            {\Large \textbf{\@university}}\\
            \vspace{0.3cm}
            {\Large \textbf{\@school}}
            
            \vspace{2cm}
            
            {\Huge \textbf{\textcolor{central_blue}{\@title}}}
            
            \if\@subtitle\empty\else
                \vspace{1cm}
                {\Large \textbf{\@subtitle}}
            \fi
            
            \if\@coursecode\empty\else
                \vspace{0.5cm}
                {\large \textbf{\if@vietnamese Mã học phần\else Course Code\fi: \@coursecode}}
            \fi
            
            \vspace{3cm}
            
            \begin{minipage}{0.45\textwidth}
                \begin{flushleft}
                    \large \textbf{\if@vietnamese Sinh viên thực hiện\else Students\fi:}\\
                    \@students
                \end{flushleft}
            \end{minipage}
            \hfill
            \begin{minipage}{0.45\textwidth}
                \begin{flushright}
                    \large \textbf{\if@vietnamese Giảng viên hướng dẫn\else Supervisors\fi:}\\
                    \@supervisors
                \end{flushright}
            \end{minipage}
            
            \vfill
            
            \if\@semester\empty\else
                {\large \textbf{\if@vietnamese Học kỳ\else Semester\fi: \@semester}}\\
            \fi
            
            \if\@academicyear\empty\else
                {\large \textbf{\if@vietnamese Năm học\else Academic Year\fi: \@academicyear}}\\
            \fi
            
            \vspace{1cm}
            {\large \textbf{\if@vietnamese Thành phố Hồ Chí Minh\else Ho Chi Minh City\fi, \today}}
        \end{center}
    \end{titlepage}
    \pageNumber
}

%--------------------------------------
% Enhanced table of contents
%--------------------------------------
\newcommand\contents{
    \renewcommand*\contentsname{\if@vietnamese MỤC LỤC\else TABLE OF CONTENTS\fi}
    \clearpage
    \phantomsection
    \addcontentsline{toc}{chapter}{\if@vietnamese MỤC LỤC\else TABLE OF CONTENTS\fi}
    \tableofcontents
    \clearpage
}

%--------------------------------------
% Enhanced list of figures
%--------------------------------------
\newcommand\listImages{
    \renewcommand*{\listfigurename}{\if@vietnamese DANH MỤC CÁC HÌNH VẼ, ĐỒ THỊ\else LIST OF FIGURES\fi}
    \clearpage
    \phantomsection
    \addcontentsline{toc}{chapter}{\if@vietnamese DANH MỤC CÁC HÌNH VẼ, ĐỒ THỊ\else LIST OF FIGURES\fi}
    
    {
        \let\oldnumberline\numberline
        \renewcommand{\numberline}{\if@vietnamese Hình~\else Figure~\fi\oldnumberline}
        \listoffigures
    }
    \clearpage
}

%--------------------------------------
% Enhanced list of tables
%--------------------------------------
\newcommand\listTables{
    \renewcommand*{\listtablename}{\if@vietnamese DANH MỤC CÁC BẢNG\else LIST OF TABLES\fi}
    \clearpage
    \phantomsection
    \addcontentsline{toc}{chapter}{\if@vietnamese DANH MỤC CÁC BẢNG\else LIST OF TABLES\fi}
    
    {
        \let\oldnumberline\numberline
        \renewcommand{\numberline}{\if@vietnamese Bảng~\else Table~\fi\oldnumberline}
        \listoftables
    }
    \clearpage
}

%--------------------------------------
% Enhanced abbreviations list
%--------------------------------------
\newlist{abbrv}{description}{1}
\setlist[abbrv,1]{
    labelwidth=3cm,
    leftmargin=3.5cm,
    itemsep=0.1\baselineskip,
    font=\bfseries
}

\newcommand{\listAbbreviations}{
    \clearpage
    \phantomsection
    \addcontentsline{toc}{chapter}{\if@vietnamese DANH MỤC TỪ VIẾT TẮT\else LIST OF ABBREVIATIONS\fi}
    \chapter*{\if@vietnamese DANH MỤC TỪ VIẾT TẮT\else LIST OF ABBREVIATIONS\fi}
}

%--------------------------------------
% Enhanced figure insertion
%--------------------------------------
\newcommand{\insertfigure}[4][0.8\textwidth]{
    \begin{figure}[H]
        \centering
        \includegraphics[width=#1]{#2}
        \caption{#3}
        \label{fig:#4}
    \end{figure}
}

\newcommand{\insertfigurehere}[4][0.8\textwidth]{
    \begin{figure}[h!]
        \centering
        \includegraphics[width=#1]{#2}
        \caption{#3}
        \label{fig:#4}
    \end{figure}
}

%--------------------------------------
% Enhanced table commands
%--------------------------------------
\newcommand{\inserttable}[4]{
    \begin{table}[H]
        \centering
        \caption{#3}
        \label{tab:#4}
        #2
    \end{table}
}

%--------------------------------------
% Enhanced bibliography
%--------------------------------------
\newcommand{\insertbibliography}[1][]{
    \clearpage
    \phantomsection
    \addcontentsline{toc}{chapter}{\if@vietnamese TÀI LIỆU THAM KHẢO\else BIBLIOGRAPHY\fi}
    \chapter*{\if@vietnamese TÀI LIỆU THAM KHẢO\else BIBLIOGRAPHY\fi}
    \if\relax\detokenize{#1}\relax
        \printbibliography[heading=none]
    \else
        \printbibliography[heading=none,#1]
    \fi
}

%--------------------------------------
% Enhanced code styling
%--------------------------------------
\lstset{
    language=Python,
    basicstyle=\ttfamily\small,
    keywordstyle=\color{central_blue}\bfseries,
    stringstyle=\color{centrale_red},
    commentstyle=\color{docs_gray}\itshape,
    numberstyle=\tiny\color{docs_gray},
    numbers=left,
    numbersep=5pt,
    stepnumber=1,
    showstringspaces=false,
    frame=leftline,
    frameround=ffff,
    framerule=2pt,
    rulecolor=\color{central_blue},
    breaklines=true,
    breakatwhitespace=true,
    tabsize=4,
    backgroundcolor=\color{docs_lightgray},
    xleftmargin=15pt,
    xrightmargin=5pt,
    captionpos=b
}

%--------------------------------------
% Enhanced code boxes
%--------------------------------------
\newtcolorbox[auto counter]{codebox}[2][]{
    enhanced,
    colback=docs_lightgray,
    colframe=central_blue,
    colbacktitle=central_blue,
    coltitle=white,
    fonttitle=\bfseries,
    boxrule=1pt,
    arc=3mm,
    drop shadow,
    title={\if@vietnamese Mã nguồn\else Code\fi~\thetcbcounter: #2},
    label={code:#1},
    breakable,
    pad at break*=1mm,
    left=3mm,
    right=3mm,
    top=1mm,
    bottom=1mm
}

%--------------------------------------
% Enhanced info boxes
%--------------------------------------
\newtcolorbox{infobox}[1][]{
    enhanced,
    colback=central_blue!5,
    colframe=central_blue,
    colbacktitle=central_blue,
    coltitle=white,
    fonttitle=\bfseries,
    boxrule=1pt,
    arc=2mm,
    title={\if@vietnamese Thông tin\else Information\fi},
    #1
}

\newtcolorbox{warningbox}[1][]{
    enhanced,
    colback=warning_orange!10,
    colframe=warning_orange,
    colbacktitle=warning_orange,
    coltitle=white,
    fonttitle=\bfseries,
    boxrule=1pt,
    arc=2mm,
    title={\if@vietnamese Cảnh báo\else Warning\fi},
    #1
}

\newtcolorbox{errorbox}[1][]{
    enhanced,
    colback=danger_red!10,
    colframe=danger_red,
    colbacktitle=danger_red,
    coltitle=white,
    fonttitle=\bfseries,
    boxrule=1pt,
    arc=2mm,
    title={\if@vietnamese Lỗi\else Error\fi},
    #1
}

\newtcolorbox{successbox}[1][]{
    enhanced,
    colback=success_green!10,
    colframe=success_green,
    colbacktitle=success_green,
    coltitle=white,
    fonttitle=\bfseries,
    boxrule=1pt,
    arc=2mm,
    title={\if@vietnamese Thành công\else Success\fi},
    #1
}

%--------------------------------------
% Mathematical theorem environments
%--------------------------------------
\theoremstyle{definition}
\newtheorem{definition}{\if@vietnamese Định nghĩa\else Definition\fi}[chapter]
\newtheorem{theorem}{\if@vietnamese Định lý\else Theorem\fi}[chapter]
\newtheorem{lemma}{\if@vietnamese Bổ đề\else Lemma\fi}[chapter]
\newtheorem{proposition}{\if@vietnamese Mệnh đề\else Proposition\fi}[chapter]
\newtheorem{corollary}{\if@vietnamese Hệ quả\else Corollary\fi}[chapter]
\newtheorem{example}{\if@vietnamese Ví dụ\else Example\fi}[chapter]
\newtheorem{remark}{\if@vietnamese Nhận xét\else Remark\fi}[chapter]

%--------------------------------------
% Enhanced appendix
%--------------------------------------
\newcommand{\startappendix}{
    \appendix
    \renewcommand{\chaptername}{\if@vietnamese Phụ lục\else Appendix\fi}
    \titleformat{\chapter}[display]
        {\bfseries\Large\centering}
        {\if@vietnamese PHỤ LỤC \thechapter\else APPENDIX \thechapter\fi}
        {0.5em}
        {\textcolor{central_blue}}
        [\vspace{0.5em}]
}

%--------------------------------------
% Draft mode features
%--------------------------------------
\if@draft
    \RequirePackage{draftwatermark}
    \SetWatermarkText{DRAFT}
    \SetWatermarkScale{1}
    \SetWatermarkColor{red!30}
    \RequirePackage{showframe}
    \RequirePackage{lineno}
    \linenumbers
\fi

%--------------------------------------
% Utility commands
%--------------------------------------
\newcommand{\todo}[1]{\textcolor{red}{\textbf{TODO: #1}}}
\newcommand{\note}[1]{\textcolor{blue}{\textbf{NOTE: #1}}}
\newcommand{\fixme}[1]{\textcolor{orange}{\textbf{FIXME: #1}}}

% Enhanced section referencing
\newcommand{\secref}[1]{Section~\ref{#1}}
\newcommand{\chapref}[1]{Chapter~\ref{#1}}
\newcommand{\figref}[1]{Figure~\ref{#1}}
\newcommand{\tabref}[1]{Table~\ref{#1}}
% \newcommand{\eqref}[1]{Equation~\ref{#1}}

% End of class
\endinput