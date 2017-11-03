import pandas as pd

from nose.tools import assert_dict_equal
from nose.tools import assert_false
from nose.tools import assert_not_in, assert_list_equal, assert_equal
from nose.tools import assert_true

from web_app.config import config_test, config
from web_app.clients.postgresql import PostgreSQLClient
from web_app.models.company import Company
from web_app.repositories.company_repository import CompanyRepositoryPSQL


class TestCompanyRepository:
    def setup(self):
        self.cursor = self.psql.cursor()

        df_mock_companies = pd.read_json(config_test['mock']['companies-sample'], orient='records')
        df_mock_companies = df_mock_companies.where((pd.notnull(df_mock_companies)), None)

        self.companies = [
            Company.from_json(row.to_dict())
            for (index, row) in df_mock_companies.iterrows()
        ]

    def teardown(self):
        self.psql.rollback()
        self.repository.drop_table()
        self.cursor.close()

    @classmethod
    def setup_class(cls):
        conn_meta = config_test['db']['postgresql']

        cls.psql = PostgreSQLClient(
            host=conn_meta['host'],
            port=conn_meta['port'],
            user=conn_meta['user'],
            dbname=conn_meta['dbname'],
            password=conn_meta['password'],
            with_dict=True
        )

        cls.repository = CompanyRepositoryPSQL(cls.psql)

    @classmethod
    def teardown_class(cls):
        cls.psql.commit()
        cls.psql.close()

    def test_create_table(self):
        """
        test that the repository successfully creates a Companies table
        """
        self.repository.create_table()

        self.cursor.execute("DELETE FROM {}".format(CompanyRepositoryPSQL.tablename))

        self.cursor.execute("SELECT COUNT(*) FROM {}".format(CompanyRepositoryPSQL.tablename))

        assert_equal(0, self.cursor.fetchone()['count'])

    def test_drop_table(self):
        """
        test that the repository successfully drops a table
        """
        self.repository.create_table()

        self.repository.drop_table()

        sql = """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        """
        self.cursor.execute(sql)

        assert_not_in((CompanyRepositoryPSQL.tablename,), self.cursor.fetchall())

    def test_insert_record(self):
        """
        test that the repository correctly inserts a record
        """

        self.repository.create_table()

        self.companies[0].id = self.repository.insert(record=self.companies[0])

        self.cursor.execute("SELECT * FROM {}".format(CompanyRepositoryPSQL.tablename))

        record = self.cursor.fetchone()

        assert_dict_equal(self.companies[0].to_json(), record)

    def test_get_record(self):
        """
        test that the repository successfully gets a record
        """
        self.repository.create_table()

        self.companies[0].id = self.repository.insert(record=self.companies[0])
        self.companies[1].id = self.repository.insert(record=self.companies[1])

        #  Primary Key is the 'ID'
        company = self.repository.get(pk=self.companies[0].id)

        assert_equal(self.companies[0], company)

    def test_find_by_name(self):

        self.repository.create_table()

        # two companies, same name
        self.companies[1].name = self.companies[0].name

        self.companies[0].id = self.repository.insert(record=self.companies[0])
        self.companies[1].id = self.repository.insert(record=self.companies[1])

        #  Primary Key is the 'ID'
        companies = self.repository.findByName(name=self.companies[1].name)

        assert_list_equal(companies, self.companies[:2])

    def test_find_by_tag(self):

        self.repository.create_table()

        for company in self.companies:
            company.id = self.repository.insert(record=company)

        tag_to_find = 'retail'

        companies = self.repository.findByTag(tag=tag_to_find)

        assert_equal(len(companies), 14)

        tag_to_find = 'eligible counterparty'

        companies = self.repository.findByTag(tag=tag_to_find)

        assert_equal(len(companies), 18)

    def test_find_by_tags(self):

        self.repository.create_table()

        for company in self.companies:
            company.id = self.repository.insert(record=company)

        tags_to_find = ['portfolio management', 'dealing on own account']

        companies = self.repository.findByAnyTag(tags=tags_to_find)

        assert_equal(len(companies), 16)

    def test_update_name(self):
        """
        Test we can update the name of a company
        """

        self.repository.create_table()

        for company in self.companies:
            company.id = self.repository.insert(record=company)

        self.repository.update_name(pk=self.companies[2].id, name="Updated Name")
        self.repository.update_name(pk=self.companies[0].id, name="Another Updated Name")

        updated_company = self.repository.get(pk=self.companies[2].id)
        another_updated_company = self.repository.get(pk=self.companies[0].id)

        assert_equal(updated_company.name, 'Updated Name')
        assert_equal(another_updated_company.name, 'Another Updated Name')

    def test_update_tags_field(self):
        """
        Test we can update a given 'tags' field with a new set of tags
        """

        self.repository.create_table()

        for company in self.companies:
            company.id = self.repository.insert(record=company)

        new_tags_1 = ['TAS_01', 'TAS_02']
        new_tags_2 = ['TIT_09', 'TIT_06']

        self.repository.update_tags_field(pk=self.companies[0].id, field='tags_ancillary_services', new_content=new_tags_1)
        self.repository.update_tags_field(pk=self.companies[1].id, field='tags_investment_types', new_content=new_tags_2)

        updated_company = self.repository.get(pk=self.companies[0].id)
        another_updated_company = self.repository.get(pk=self.companies[1].id)

        assert_equal(updated_company.tags_ancillary_services, new_tags_1)
        assert_equal(another_updated_company.tags_investment_types, new_tags_2)

    def test_count_records(self):

        self.repository.create_table()

        for company in self.companies:
            company.id = self.repository.insert(record=company)

        number_records = self.repository.count()

        assert_equal(number_records, 20)

    def test_list_all_with_pagination(self):
        """
        Test that the pagination logic is working properly by returning the correct number of results as well
        as signaling the 'has_prev' and 'has_next'
        """

        page = 1
        results_per_page = 5

        self.repository.create_table()

        for company in self.companies:
            company.id = self.repository.insert(record=company)

        page_results, has_prev, has_next = self.repository.get_all(page=page, per_page=results_per_page)

        assert_equal(len(page_results), results_per_page)

        assert_list_equal(page_results, self.companies[:results_per_page])

        assert_false(has_prev)
        assert_true(has_next)

    def test_list_all_with_pagination_2(self):
        """
        Test that the pagination logic is working properly by returning the correct number of results as well
        as signaling the 'has_prev' and 'has_next'
        """

        page = 2
        results_per_page = 7

        self.repository.create_table()

        for company in self.companies:
            company.id = self.repository.insert(record=company)

        page_results, has_prev, has_next = \
            self.repository.get_all(page=page, per_page=results_per_page)

        assert_equal(len(page_results), results_per_page)

        assert_list_equal(page_results, self.companies[(page - 1) * results_per_page:page * results_per_page])

        assert_true(has_prev)
        assert_true(has_next)

    def test_list_all_with_pagination_3(self):
        """
        Test that the pagination logic is working properly by returning the correct number of results as well
        as signaling the 'has_prev' and 'has_next'
        """

        page = 4
        results_per_page = 5

        self.repository.create_table()

        for company in self.companies:
            company.id = self.repository.insert(record=company)

        page_results, has_prev, has_next = \
            self.repository.get_all(page=page, per_page=results_per_page)

        assert_equal(len(page_results), results_per_page)

        assert_list_equal(page_results, self.companies[(page - 1) * results_per_page:page * results_per_page])

        assert_true(has_prev)
        assert_false(has_next)

    def test_list_all_with_pagination_4(self):
        """
        Test that the pagination logic is working properly by returning the correct number of results as well
        as signaling the 'has_prev' and 'has_next'

        If we request a high number page, i.e. page_number=100 and the table just has 20 rows, it should return
        None, false, false
        """

        page = 100
        results_per_page = 5

        self.repository.create_table()

        for company in self.companies:
            company.id = self.repository.insert(record=company)

        page_results, has_prev, has_next = \
            self.repository.get_all(page=page, per_page=results_per_page)

        assert_list_equal(page_results, [])

        assert_false(has_prev)
        assert_false(has_next)

    def test_list_all_with_pagination_5(self):
        """
        Test that the pagination logic is working properly by returning the correct number of results as well
        as signaling the 'has_prev' and 'has_next'

        If we request a page that does not have results,but the previous has, we should signal it
        None, True, False
        """

        page = 5
        results_per_page = 5

        self.repository.create_table()

        for company in self.companies:
            company.id = self.repository.insert(record=company)

        page_results, has_prev, has_next = \
            self.repository.get_all(page=page, per_page=results_per_page)

        assert_list_equal(page_results, [])

        assert_true(has_prev)
        assert_false(has_next)

    def test_update_record(self):
        """
        Test that we can update a complete row of a company
        """
        self.repository.create_table()

        for company in self.companies:
            company.id = self.repository.insert(record=company)

        self.repository.update(pk=1, updated_record=self.companies[-1])

        updated_company = self.repository.get(pk=1)
        self.companies[-1].id = 1

        assert_equal(updated_company, self.companies[-1])

    def test_delete_record(self):

        self.repository.create_table()

        for company in self.companies:
            company.id = self.repository.insert(record=company)

        self.repository.delete(self.companies[0].id)

        company = self.repository.get(self.companies[0].id)

        assert_equal(company, None)
