import os

from openai_api.repository.openai_api_repository_impl import OpenaiApiRepositoryImpl
from openai_api.service.open_ai_service import OpenaiApiService
from preprocessing.repository.preprocessing_repository_impl import PreprocessingRepositoryImpl


class OpenaiApiServiceImpl(OpenaiApiService):
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.__openaiApiRepository = OpenaiApiRepositoryImpl.getInstance()
            cls.__instance.__preprocessingRepository = PreprocessingRepositoryImpl.getInstance()

        return cls.__instance

    @classmethod
    def getInstance(cls):
        if cls.__instance is None:
            cls.__instance = cls()

        return cls.__instance

    async def letsChat(self, *arg, **kwargs):
        userSendMessage = arg[0]
        fileKey = arg[1]
        print(f"service -> letsChat() userSendMessage: {userSendMessage}")
        print(f"service -> letsChat() fileKey: {fileKey}")
        mainText = None

        if not os.path.exists(os.path.join(os.getcwd(), "vectorstore")):
            os.mkdir(os.path.join(os.getcwd(), "vectorstore"))

        if not os.path.exists(os.path.join(os.getcwd(), "download_pdfs")):
            os.mkdir(os.path.join(os.getcwd(), "download_pdfs"))

        if fileKey is not None:
            DOWNLOAD_PATH = "download_pdfs"
            FILE_PATH = os.path.join(os.getcwd(), DOWNLOAD_PATH, fileKey)

            if not os.path.exists(FILE_PATH):
                await self.__preprocessingRepository.downloadFileFromS3(fileKey)
                print("finish to download file")

            text = self.__preprocessingRepository.extractTextFromPDFToMarkdown(FILE_PATH)
            print("finish to extract pdf to markdown")

            mainText, _ = self.__preprocessingRepository.separateMainAndReferences(text)
            print("finish to separate main and references")

            documentList = self.__preprocessingRepository.splitTextIntoDocuments(mainText)
            print("finish to split text")

            dbPath = os.path.join(os.getcwd(), "vectorstore", fileKey.split(".")[0])
            if os.path.exists(dbPath):
                vectorstore = self.__preprocessingRepository.loadFAISS(dbPath)
            else:
                vectorstore = self.__preprocessingRepository.createFAISS(documentList)
                print("finish to create FAISS")
                self.__preprocessingRepository.saveFAISS(vectorstore, dbPath)

        else:
            vectorstore = None

        return self.__openaiApiRepository.generateText(userSendMessage, vectorstore, fileKey, mainText)

