from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Publisher(Base):
    __tablename__ = 'publisher'
    id_document = Column(Integer, primary_key=True)
    publisher = Column(String, nullable=False)


class IssnPublisher(Base):
    __tablename__ = 'issn_publisher'
    issn = Column(String, primary_key=True)
    publisher = Column(String, nullable=False)


class EissnPublisher(Base):
    __tablename__ = 'eissn_publisher'
    eissn = Column(String, primary_key=True)
    publisher = Column(String, nullable=False)


class IssnImpact(Base):
    __tablename__ = 'issn_impact'
    issn = Column(String, primary_key=True)
    citeScoreCurrentMetric = Column(Float, nullable=False)
    citeScoreCurrentMetricYear = Column(Integer, nullable=False)
    citeScoreTracker = Column(Float, nullable=False)
    citeScoreTrackerYear = Column(Date, nullable=False)
    sjrMetric = Column(Float, nullable=False)
    sjrYear = Column(Integer, nullable=False)


class Document(Base):
    __tablename__ = 'documents'
    id_document = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    abstract = Column(String)
    keywords = Column(String)
    author = Column(String)
    published_date = Column(Date)
    doi = Column(String, unique=True)
    eid = Column(String, unique=True)
    publication_name = Column(String)
    issn = Column(String, ForeignKey('issn_publisher.issn'))
    eissn = Column(String, ForeignKey('eissn_publisher.eissn'))
    type = Column(String)
    sub_type = Column(String)
    search_query = Column(String)
    source = Column(String)
    affiliation_country = Column(String)
    citedby_count = Column(Integer)


class DoiEurl(Base):
    __tablename__ = 'doi_eurl'
    doi = Column(String, primary_key=True)
    eurl = Column(String, nullable=False)


class Continent(Base):
    __tablename__ = 'continents'
    affiliation_country = Column(String, primary_key=True)
    continent = Column(String, nullable=False)


class AggregatedPublisher(Base):
    __tablename__ = 'aggregated_publisher'
    publisher = Column(String, primary_key=True)
    aggregated_publisher = Column(String, nullable=False)


class Manuscript(Base):
    __tablename__ = 'manuscript'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    abstract = Column(String)
    keywords = Column(String)
    author = Column(String)
    published_date = Column(Date)
    doi = Column(String)
    eid = Column(String)
    publication_name = Column(String)
    issn = Column(String)
    eissn = Column(String)
    type = Column(String)
    sub_type = Column(String)
    search_query = Column(String)
    source = Column(String)
    affiliation_country = Column(String)
    citedby_count = Column(Integer)


class Journal(Base):
    __tablename__ = 'journal'
    id = Column(Integer, primary_key=True)
    issn = Column(String)
    citeScoreCurrentMetric = Column(Float)
    citeScoreCurrentMetricYear = Column(Integer)
    citeScoreTracker = Column(Float)
    citeScoreTrackerYear = Column(Date)
    sjrMetric = Column(Float)
    sjrYear = Column(Integer)
