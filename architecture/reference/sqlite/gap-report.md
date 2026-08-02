# SQLite reference dry-run

This synthetic candidate proves the single-instance/local-disk/WAL/backup profile contract. It did
not open a database or inspect business data. It is **DRY-RUN CANDIDATE / NOT DEPLOYED**. A real project
must prove one writer, local filesystem, bounded contention, capacity, online backup checksum and a
semi-annual restore drill; otherwise it must select PostgreSQL through an independent Change.
