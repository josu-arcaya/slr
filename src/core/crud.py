import logging

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased

from core.database import Database
from core.models import (
    Continent,
    Document,
    DoiEurl,
    EissnPublisher,
    IssnImpact,
    IssnPublisher,
    Publisher,
    StudySelection,
)

LOGGER = logging.getLogger(__name__)


class SqlAlchemyORM:
    def __init__(self, db_name="documents.db"):
        self.db = Database(db_name)

    def get_impact_by_issn(self, issn: str):
        # This function gets the impact by ISSN
        with self.db.get_session() as sess:
            issn_impact_alias = aliased(IssnImpact)
            result = sess.query(issn_impact_alias).filter(issn_impact_alias.issn == issn).first()

            if result:
                return {
                    "issn": result.issn,
                    "citeScoreCurrentMetric": result.citeScoreCurrentMetric,
                    "citeScoreCurrentMetricYear": result.citeScoreCurrentMetricYear,
                    "citeScoreTracker": result.citeScoreTracker,
                    "citeScoreTrackerYear": result.citeScoreTrackerYear,
                    "sjrMetric": result.sjrMetric,
                    "sjrYear": result.sjrYear,
                }
            else:
                return None

    def set_impact_by_issn(
        # This function sets the impact by ISSN
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
        # This function gets the publisher by ISSN
        with self.db.get_session() as sess:
            result = sess.execute(select(IssnPublisher).filter_by(issn=issn)).first()
            if result:
                return {
                    "issn": result[0].issn,
                    "publisher": result[0].publisher,
                }
            else:
                return None

    def set_publisher_by_issn(self, issn: str, publisher: str):
        # This function sets the publisher by ISSN
        with self.db.get_session() as sess:
            issn_publisher = IssnPublisher(issn=issn, publisher=publisher)
            sess.add(issn_publisher)
            sess.commit()

    def get_publisher_by_eissn(self, eissn: str):
        # This function gets the publisher by EISSN
        with self.db.get_session() as sess:
            result = sess.execute(select(EissnPublisher).filter_by(eissn=eissn)).first()
            if result:
                return {
                    "eissn": result[0].eissn,
                    "publisher": result[0].publisher,
                }
            else:
                return None

    def set_publisher_by_eissn(self, eissn: str, publisher: str):
        # This function sets the publisher by EISSN
        with self.db.get_session() as sess:
            eissn_publisher = EissnPublisher(eissn=eissn, publisher=publisher)
            sess.add(eissn_publisher)
            sess.commit()

    def save(self, documents):
        # This function saves documents in the database
        with self.db.get_session() as sess:
            for doc in documents:
                try:
                    sess.add(doc)
                    sess.commit()
                    LOGGER.info("Document inserted successfully")
                except IntegrityError:
                    LOGGER.warning("Failed to insert document, it already exists.")
                    sess.rollback()

    def get_all_issn_without_publisher(self):
        # This function gets the documents with ISSN but without editor
        with self.db.get_session() as sess:
            result = (
                sess.query(Document.eid, Document.issn, Document.eissn)
                .outerjoin(
                    IssnPublisher,
                    Document.issn.__eq__(IssnPublisher.issn),
                )
                .filter(
                    IssnPublisher.publisher.is_(None),
                    Document.issn.isnot(None),
                )
                .all()
            )
            return [(row[0], row[1], row[2]) for row in result]

    def get_all_eissn_without_publisher(self):
        # This function gets the documents with EISSN but without editorr
        with self.db.get_session() as sess:
            result = (
                sess.query(Document.eid, Document.issn, Document.eissn)
                .outerjoin(
                    EissnPublisher,
                    Document.eissn.__eq__(EissnPublisher.eissn),
                )
                .filter(
                    EissnPublisher.publisher.is_(None),
                    Document.eissn.isnot(None),
                )
                .all()
            )
            return [(row[0], row[1], row[2]) for row in result]

    def get_empty_publisher(self):
        # This function gets the documents without a publisher
        with self.db.get_session() as sess:
            result = (
                sess.query(
                    Document.id_document,
                    Document.eid,
                    Document.issn,
                    Document.eissn,
                )
                .outerjoin(
                    IssnPublisher,
                    Document.issn.__eq__(IssnPublisher.issn),
                )
                .filter(IssnPublisher.publisher.is_(None))
                .all()
            )
            return [(row[0], row[1], row[2]) for row in result]

    def set_publisher(self, publishers):
        # This function sets the publisher for documents
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
        # Function to retrieve affiliation countries from
        # documents that have no corresponding continent information
        with self.db.get_session() as sess:
            result = (
                sess.query(Document.affiliation_country.distinct())
                .outerjoin(
                    Continent,
                    Document.affiliation_country.__eq__(Continent.affiliation_country),
                )
                .filter(
                    Continent.continent.is_(None),
                    Document.affiliation_country.isnot(None),
                )
                .all()
            )
            return [(row[0]) for row in result]

    def set_continent(self, tuples):
        # This function sets the continent for affiliated countries
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
        # This function gets documents with DOI without access URL
        with self.db.get_session() as sess:
            result = (
                sess.query(Document.doi)
                .outerjoin(DoiEurl, Document.doi.__eq__(DoiEurl.doi))
                .filter(Document.doi.isnot(None), DoiEurl.eurl.is_(None))
                .all()
            )
            return [(row[0]) for row in result]

    def set_doi_eurl(self, doi: str, eurl: str):
        # This function sets the access URL for documents with DOI
        with self.db.get_session() as sess:
            doi_eurl = DoiEurl(doi=doi, eurl=eurl)
            sess.add(doi_eurl)
            sess.commit()

    def get_empty_openaccess(self):
        # This function gets documents without openaccess
        # and with status 3 in StudySelection
        with self.db.get_session() as sess:
            subquery = sess.query(StudySelection.id_document).filter(StudySelection.status == 3).subquery()

            doc = aliased(Document)

            result = (
                sess.query(doc.eid)
                .join(
                    subquery,
                    doc.id_document.__eq__(subquery.scalar_subquery()),
                )
                .filter(doc.openaccess is None)
                .all()
            )

            return [(row[0]) for row in result]

    def set_openaccess(self, eid: str, openaccess: str):
        # This method updates the openaccess field of
        # a document in the database.
        with self.db.get_session() as sess:
            try:
                stmt = update(Document).where(Document.eid.__eq__(eid)).values(openaccess=openaccess)
                sess.execute(stmt)

                LOGGER.info("Field openaccess updated successfully")
            except Exception as error:
                LOGGER.error(f"Failed to update openaccess, {error}.")
                exit(-1)

    def set_status_studyselection(self, document_id: int, status: int):
        # This method updates the status of the study selection
        # related to a document in the database.
        with self.db.get_session() as sess:
            try:
                study_selection = sess.query(StudySelection).filter_by(id_document=document_id).first()

                if study_selection:
                    study_selection.status = status
                    sess.commit()
                    LOGGER.info("Status of study selection updated successfully")
                else:
                    LOGGER.error("Study selection not found for the given document ID")
            except Exception as error:
                LOGGER.error(f"Failed to update status of study selection, {error}.")
                exit(-1)

    def get_documents_country(self):
        # This function gets the country value of every entry
        with self.db.get_session() as sess:
            result = sess.query(Document.affiliation_country).all()
            return [(row[0]) for row in result]

    def get_documents_eid(self):
        # This function gets the eid value of every document
        with self.db.get_session() as sess:
            result = sess.query(Document.eid).all()
            return [(row[0]) for row in result]

    def get_documents_id_abstract(self):
        # This function gets the relation between document abstract and it identificator
        with self.db.get_session() as sess:
            result = sess.query(Document.id_document, Document.abstract).all()
            return [(row[0], row[1]) for row in result]

    def get_documents_type(self):
        with self.db.get_session() as sess:
            result = (
                sess.query(
                    Document.sub_type,  # El tipo de documento
                    func.count().label("cantidad"),  # Contar el número de documentos por tipo
                )
                .group_by(Document.sub_type)  # Agrupar por el tipo de documento
                .all()  # Ejecutamos la consulta y obtenemos todos los resultados
            )

        return result

    def get_documents_year(self):
        with self.db.get_session() as sess:
            result = (
                sess.query(
                    func.substr(Document.published_date, 1, 4).label("año"),  # Extraer el año de la fecha
                    func.count().label("cantidad"),  # Contar el número de documentos
                )
                .group_by(func.substr(Document.published_date, 1, 4))  # Agrupar por el año
                .all()  # Ejecutamos la consulta y obtenemos todos los resultados
            )

        return result

    def insert_publisher(self, eid: str, complete_name: str, author: dict):
        # This function inserts a publisher in the database
        with self.db.get_session() as sess:
            publisher = Publisher(
                id_document=eid,
                complete_name=complete_name,
                auid=author["auid"],
                document_number=author["document_count"],
                cited_by_count=author["cited_by_count"],
                citation_count=author["citation_count"],
                creation_date=author["creation_date"],
                publication_range=author["publication_range"],
                country=author["country"],
                city=author["city"],
            )

        # Agregar la instancia a la sesión
        sess.add(publisher)

        # Confirmar la transacción (commit)
        sess.commit()
