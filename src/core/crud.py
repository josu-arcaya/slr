import logging
from datetime import datetime
from collections import namedtuple
from models import Base, Publisher, IssnPublisher, EissnPublisher, IssnImpact, Document, DoiEurl, Continent, \
    AggregatedPublisher, Manuscript, Journal
from database import Database
from sqlalchemy import create_engine, MetaData, select
from sqlalchemy.orm import sessionmaker, Session, aliased
from sqlalchemy.exc import IntegrityError

Manuscript = namedtuple(
    "Manuscript",
    "title abstract keywords author published_date doi eid publication_name issn eissn type sub_type search_query source, affiliation_country, citedby_count",
)

Journal = namedtuple(
    "Journal",
    "issn citeScoreCurrentMetric citeScoreCurrentMetricYear citeScoreTracker citeScoreTrackerYear sjrMetric sjrYear",
)

LOGGER = logging.getLogger("systematic")


class SqlAlchemyORM:
    def __init__(self, db_name="documents.db"):
        self.db = Database(db_name)

    def get_impact_by_issn(self, issn: str):
        # Obtiene el impacto por ISSN
        with self.db.get_session() as sess:
            issn_impact_alias = aliased(IssnImpact)
            result = (
                sess.query(issn_impact_alias)
                .filter(issn_impact_alias.issn == issn)
                .first()
            )

            if result:
                return {
                    'issn': result.issn,
                    'citeScoreCurrentMetric': result.citeScoreCurrentMetric,
                    'citeScoreCurrentMetricYear': result.citeScoreCurrentMetricYear,
                    'citeScoreTracker': result.citeScoreTracker,
                    'citeScoreTrackerYear': result.citeScoreTrackerYear,
                    'sjrMetric': result.sjrMetric,
                    'sjrYear': result.sjrYear,
                }
            else:
                return None

    def set_impact_by_issn(
            # Establece el impacto por ISSN
            self,
            issn: str,
            citeScoreCurrentMetric: float,
            citeScoreCurrentMetricYear: int,
            citeScoreTracker: float,
            citeScoreTrackerYear: int,
            sjrMetric: float,
            sjrYear: int,
    ):
        with self.db.get_session() as sess:
            issn_impact = IssnImpact(
                issn=issn,
                citeScoreCurrentMetric=citeScoreCurrentMetric,
                citeScoreCurrentMetricYear=citeScoreCurrentMetricYear,
                citeScoreTracker=citeScoreTracker,
                citeScoreTrackerYear=citeScoreTrackerYear,
                sjrMetric=sjrMetric,
                sjrYear=sjrYear,
            )
            sess.add(issn_impact)
            sess.commit()

    def get_publisher_by_issn(self, issn: str):
        # Obtiene el editor (publisher) por ISSN
        with self.db.get_session() as sess:
            result = sess.execute(select(IssnPublisher).filter_by(issn=issn)).first()
            if result:
                return {'issn': result[0].issn, 'publisher': result[0].publisher}
            else:
                return None

    def set_publisher_by_issn(self, issn: str, publisher: str):
        # Establece el editor (publisher) por ISSN
        with self.db.get_session() as sess:
            issn_publisher = IssnPublisher(issn=issn, publisher=publisher)
            sess.add(issn_publisher)
            sess.commit()

    def get_publisher_by_eissn(self, eissn: str):
        # Obtiene el editor (publisher) por EISSN
        with self.db.get_session() as sess:
            result = sess.execute(select(EissnPublisher).filter_by(eissn=eissn)).first()
            if result:
                return {'eissn': result[0].eissn, 'publisher': result[0].publisher}
            else:
                return None

    def set_publisher_by_eissn(self, eissn: str, publisher: str):
        # Establece el editor (publisher) por EISSN
        with self.db.get_session() as sess:
            eissn_publisher = EissnPublisher(eissn=eissn, publisher=publisher)
            sess.add(eissn_publisher)
            sess.commit()

    def save(self, documents):
        # Guarda documentos en la base de datos
        with self.db.get_session() as sess:
            try:
                for doc in documents:
                    document = Document(
                        title=doc[0],
                        abstract=doc[1],
                        keywords=doc[2],
                        author=doc[3],
                        published_date=datetime.strptime(doc[4], "%Y-%m-%d"),
                        doi=doc[5],
                        eid=doc[6],
                        publication_name=doc[7],
                        issn=doc[8],
                        eissn=doc[9],
                        type=doc[10],
                        sub_type=doc[11],
                        search_query=doc[12],
                        source=doc[13],
                        affiliation_country=doc[14],
                        citedby_count=doc[15],
                    )
                    sess.add(document)
                sess.commit()
                LOGGER.info("Document inserted successfully")
            except IntegrityError as error:
                LOGGER.error(f"Failed to insert document, {error}.")
                exit(-1)

    def get_all_issn_without_publisher(self):
        # Obtiene los documentos con ISSN pero sin editor
        with self.db.get_session() as sess:
            result = (
                sess.query(Document.eid, Document.issn, Document.eissn)
                .outerjoin(IssnPublisher, Document.issn.__eq__(IssnPublisher.issn))
                .filter(IssnPublisher.publisher.is_(None), Document.issn.isnot(None))
                .all()
            )
            return [(row[0], row[1], row[2]) for row in result]

    def get_all_eissn_without_publisher(self):
        # Obtiene los documentos con EISSN pero sin editor
        with self.db.get_session() as sess:
            result = (
                sess.query(Document.eid, Document.issn, Document.eissn)
                .outerjoin(EissnPublisher, Document.eissn.__eq__(EissnPublisher.eissn))
                .filter(EissnPublisher.publisher.is_(None), Document.eissn.isnot(None))
                .all()
            )
            return [(row[0], row[1], row[2]) for row in result]

    def get_empty_publisher(self):
        # Obtiene los documentos sin editor
        with self.db.get_session() as sess:
            result = (
                sess.query(Document.id_document, Document.eid, Document.issn, Document.eissn)
                .outerjoin(IssnPublisher, Document.issn.__eq__(IssnPublisher.issn))
                .filter(IssnPublisher.publisher.is_(None))
                .all()
            )
            return [(row[0], row[1], row[2]) for row in result]

    def set_publisher(self, publishers):
        # Establece el editor para documentos
        with self.db.get_session() as sess:
            try:
                for publisher in publishers:
                    issn_publisher = IssnPublisher(issn=publisher[0], publisher=publisher[1])
                    sess.add(issn_publisher)
                sess.commit()
                LOGGER.info("Publisher inserted successfully")
            except IntegrityError as error:
                LOGGER.error(f"Failed to insert publisher, {error}.")
                exit(-1)

    def get_empty_continents(self):
        # Obtiene los países afiliados a documentos que no tienen asignado un continente
        with self.db.get_session() as sess:
            result = (
                sess.query(Document.affiliation_country.distinct())
                .outerjoin(Continent, Document.affiliation_country.__eq__(Continent.affiliation_country))
                .filter(Continent.continent.is_(None), Document.affiliation_country.isnot(None))
                .all()
            )
            return [(row[0]) for row in result]

    def set_continent(self, tuples):
        # Establece el continente para países afiliados a documentos
        with self.db.get_session() as sess:
            try:
                for tpl in tuples:
                    continent = Continent(affiliation_country=tpl[0], continent=tpl[1])
                    sess.add(continent)
                sess.commit()
                LOGGER.info("Continent inserted successfully")
            except IntegrityError as error:
                LOGGER.error(f"Failed to insert continent, {error}.")
                exit(-1)

    def get_doi(self):
        # Obtiene los documentos con DOI sin URL de acceso
        with self.db.get_session() as sess:
            result = (
                sess.query(Document.doi)
                .outerjoin(DoiEurl, Document.doi.__eq__(DoiEurl.doi))
                .filter(Document.doi.isnot(None), DoiEurl.eurl.is_(None))
                .all()
            )
            return [(row[0]) for row in result]

    def set_doi_eurl(self, doi: str, eurl: str):
        # Establece la URL de acceso para documentos con DOI
        with self.db.get_session() as sess:
            doi_eurl = DoiEurl(doi=doi, eurl=eurl)
            sess.add(doi_eurl)
            sess.commit()

    def get_empty_openaccess(self):
        # Obtiene documentos sin acceso abierto y con status 3 en StudySelection
        with self.db.get_session() as sess:
            subquery = (
                # No se define StudySelection, actualmente no existe el modelo.
                sess.query(StudySelection.id_document)
                .filter(StudySelection.status == 3)
                .subquery()
            )

            documents_alias = aliased(Document)

            result = (
                sess.query(documents_alias.eid)
                .join(subquery, documents_alias.id_document.__eq__(subquery))
                .filter(documents_alias.openaccess.is_(None))
                .all()
            )

            return [(row[0]) for row in result]


# Prueba de funcionamiento del ORM SQLAlchemy
if __name__ == "__main__":
    # Crear una instancia de SqlAlchemyORM
    sqlalchemy = SqlAlchemyORM()
    print(sqlalchemy.db.engine)

    # Obtener una sesión de SQLAlchemy
    session = sqlalchemy.db.get_session()

    # new_publisher = Publisher(id_document=1, publisher="Nuevo editor")
    # session.add(new_publisher)
    # session.commit()
    print("Tablas en la base de datos:")
    metadata = MetaData()
    metadata.reflect(bind=sqlalchemy.db.engine)
    print(metadata.tables.keys())

    sqlalchemy.set_publisher_by_issn("1234-5678", "Nuevo editor")
    print("Publisher set successfully")

    # Función get_publisher_by_issn
    publisher = sqlalchemy.get_publisher_by_issn("1234-5678")
    print(f"Publisher: {publisher}")

    # Función set_impact_by_issn
    sqlalchemy.set_impact_by_issn("1234-5678", 1.0, 2022, 1.1, 2023, 1.2, 2022)
    print("Impact set successfully")

    # Función get_impact_by_issn
    impact = sqlalchemy.get_impact_by_issn("1234-5678")
    print(f"Impact: {impact}")

    # Función set_publisher_by_eissn
    sqlalchemy.set_publisher_by_eissn("5678-1234", "Nuevo editor")
    print("eISSN Publisher set successfully")

    # Función get_publisher_by_eissn
    eissn_publisher = sqlalchemy.get_publisher_by_eissn("5678-1234")
    print(f"eISSN Publisher: {eissn_publisher}")

    # Función save
    documents = [(
        "title", "abstract", "keywords", "author", "2022-01-01", "doi", "eid", "publication_name", "1234-5678",
        "5678-1234", "type", "sub_type", "search_query", "source", "affiliation_country", 0)]
    sqlalchemy.save(documents)
    print("Documents saved successfully")

    # Prueba de la función get_all_issn_without_publisher
    result = sqlalchemy.get_all_issn_without_publisher()
    print(f"Resultado de get_all_issn_without_publisher: {result}")

    # Prueba de la función get_all_eissn_without_publisher
    result = sqlalchemy.get_all_eissn_without_publisher()
    print(f"Resultado de get_all_eissn_without_publisher: {result}")

    # Prueba de la función get_empty_publisher
    result = sqlalchemy.get_empty_publisher()
    print(f"Resultado de get_empty_publisher: {result}")

    # Prueba de la función set_publisher
    publishers = [(1, 'publisher1'), (2, 'publisher2')]
    sqlalchemy.set_publisher(publishers)

    # Prueba de la función set_continent
    tuples = [('Spain', 'Europe'), ('Japan', 'Asia')]
    sqlalchemy.set_continent(tuples)

    # Prueba de la función get_empty_continents
    result = sqlalchemy.get_empty_continents()
    print(f"Resultado de get_empty_continents: {result}")

    # Prueba de la función set_doi_eurl
    sqlalchemy.set_doi_eurl("10.1000/xyz123", "http://example.com")

    # Prueba de la función get_doi
    result = sqlalchemy.get_doi()
    print(f"Resultado de get_doi: {result}")

    session.close()
