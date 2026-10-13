import { ExternalLink, Link2 } from "lucide-react";

export interface SourceItem {
    id: string;
    title: string;
    description: string;
    url: string;
}

interface SourceListProps {
    sources: SourceItem[];
}

function SourceList({ sources }: SourceListProps) {
    if (sources.length === 0) {
        return null;
    }

    return (
        <div className="source-list">
            <div className="source-list__title">
                <Link2 size={14} />
                <span>Sumber jawaban</span>
            </div>

            <div className="source-list__items">
                {sources.map((source, index) => (
                    <a
                        key={source.id}
                        className="source-list__item"
                        href={source.url}
                        target="_blank"
                        rel="noreferrer"
                    >
                        <span className="source-list__number">{index + 1}</span>

                        <span className="source-list__content">
                            <strong>{source.title}</strong>
                            <small>{source.description}</small>
                        </span>

                        <ExternalLink
                            className="source-list__external"
                            size={15}
                        />
                    </a>
                ))}
            </div>
        </div>
    );
}

export default SourceList;